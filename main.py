#!/usr/bin/env python3

'''
    LinWisp: A simple AI assistant for Linux using Google Gemini and OpenAI Whisper.
    This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
'''

import numpy as np
import argparse
import subprocess
import signal

from core import load_config, save_config, load_api_key, save_api_key, ask_ai

def record_sound(
    aggressiveness=2,
    sample_rate=16000,
    frame_duration=30,  # ms
    silence_timeout=1.0  # seconds of silence before stopping
):
    import whisper
    import webrtcvad
    import collections
    import sounddevice as sd
    
    vad = webrtcvad.Vad(aggressiveness)
    frame_size = int(sample_rate * frame_duration / 1000)
    silence_limit = int(silence_timeout * 1000 / frame_duration)

    ring_buffer = collections.deque(maxlen=silence_limit)
    audio_frames = []

    print("Listening...")
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
        while True:
            audio = stream.read(frame_size)[0].flatten()
            frame_bytes = audio.tobytes()
            is_speaking = vad.is_speech(frame_bytes, sample_rate)

            audio_frames.append(audio)
            ring_buffer.append(is_speaking)

            if not any(ring_buffer):
                break

    # Stack frames and normalize
    audio_array = np.concatenate(audio_frames).astype(np.float32) / 32768.0

    model = whisper.load_model("base")
    result = model.transcribe(audio_array, fp16=False)
    return result['text'].strip()

def update_config(args):
    config = load_config()
    updated = False

    if args.model:
        config["model"] = args.model
        print(f"Model set to {args.model}.")
        updated = True

    if args.gui:
        if not config.get("gui"):
            config["gui"] = True
        else:
            config["gui"] = False
        updated = True

    if updated:
        save_config(config)

def prompt_input(gui_mode):
    if gui_mode:
        result = subprocess.run("zenity --entry --title='LinWisp' --text='Enter your prompt:'", capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    else:
        return input("Enter your prompt: ").strip()

def confirm_prompt_empty(gui_mode):
    if gui_mode:
        confirm = subprocess.run("zenity --question --title='LinWisp' --text='Empty prompt. Are you sure?'", shell=True)
        return confirm.returncode == 0
    else:
        return input("Empty prompt. Are you sure? (y/n): ").strip().lower() == 'y'

def launch_tray(args):
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        try:
            gi.require_version('AyatanaAppIndicator3', '0.1')
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3
        except (ImportError, ValueError):
            gi.require_version('AppIndicator3', '0.1')
            from gi.repository import AppIndicator3

        from functools import partial

        APP_ID = "LinWisp.Tray"

        def on_prompt(method, _):
            config = load_config()
            api_key = args.apikey or load_api_key()
            model = args.model or config.get("model")

            if not api_key:
                print("API key is required. Set it using --apikey.")
                subprocess.run("zenity --error --text='API key is required. Set it using --apikey.'")
                exit(1)

            if not model:
                print("Model is required. Set it using --model or edit config.toml.")
                subprocess.run("zenity --error --text='Model is required. Set it using --model or edit config.toml.'")
                exit(1)

            if method == "speak":
                prompt = record_sound()
                if not prompt:
                    return
            else:
                prompt = prompt_input(True)
                if not prompt:
                    return
            try:
                response = ask_ai(prompt, api_key, model)
                if method == "speak":
                    subprocess.run(["espeak", "-s", "150", "-v", "en-us", response])
                subprocess.run(["zenity", "--text-info", "--title=LinWisp", "--width=600", "--height=400", "--no-wrap"], input=response, text=True, shell=True)
            except Exception as e:
                subprocess.run(["zenity", "--error", "--title=LinWisp", "--text", str(e)], shell=True)

        def on_quit(_):
            Gtk.main_quit()
            exit(0)

        indicator = AppIndicator3.Indicator.new(
            APP_ID, "accessories-text-editor-symbolic",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        menu = Gtk.Menu()

        prompt_item = Gtk.MenuItem(label="Type to LinWisp")
        prompt_item.connect("activate", partial(on_prompt, "type"))
        prompt_item.show()
        menu.append(prompt_item)

        record_item = Gtk.MenuItem(label="Record to LinWisp")
        record_item.connect("activate", partial(on_prompt, "speak"))
        record_item.show()
        menu.append(record_item)

        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", on_quit)
        quit_item.show()
        menu.append(quit_item)

        indicator.set_menu(menu)

        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()
    except Exception as e:
        print(f"Failed to launch tray: {e}")
        exit(1)

def main_cli(args):
    config = load_config()
    api_key = args.apikey or load_api_key()
    model = args.model or config.get("model")
    gui_mode = config.get("gui", False)

    if not api_key:
        print("API key is required. Set it using --apikey.")
        subprocess.run("zenity --error --text='API key is required. Set it using --apikey.'", shell=True)
        exit(1)

    if not model:
        print("Model is required. Set it using --model or edit config.toml.")
        subprocess.run("zenity --error --text='Model is required. Set it using --model or edit config.toml.'", shell=True)
        exit(1)

    if args.record:
        prompt = record_sound()
        print(f"Recorded prompt: {prompt}")
    else:
        prompt = prompt_input(gui_mode)
    if not prompt and not confirm_prompt_empty(gui_mode):
        return
    
    try:
        response = ask_ai(prompt, api_key, model)
        if args.record:
            subprocess.run(["espeak", "-s", "150", "-v", "en-us", response])
        if gui_mode:
            subprocess.run(["zenity", "--text-info", "--title=LinWisp", "--width=600", "--height=400", "--no-wrap"], input=response, text=True)
        else:
            print(response)
    except Exception as e:
        print(f"An error occurred: {e}")
        if gui_mode:
            subprocess.run(["zenity", "--error", "--text", f"An error occurred: {e}"], shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinWisp: A simple AI assistant for Linux using Google Gemini and OpenAI Whisper.")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("--model", type=str, help="Specify the model to use. Defaults to the one in config.toml.")
    parser.add_argument("--gui", action="store_true", help="Toggle between GUI (Zenity) and CLI.")
    parser.add_argument("--apikey", type=str, help="Set the API key. Replaces the existing one if provided.")
    group.add_argument("--tray", action="store_true", help="Launch as a system tray application.")
    group.add_argument("--record", action="store_true", help="Record (instead of typing) the prompt.")
    args = parser.parse_args()

    if args.apikey:
        save_api_key(args.apikey)

    if args.apikey and load_api_key() == args.apikey:
        print("Hint: You don't need to define --apikey every single time you run LinWisp.")

    update_config(args)

    if args.tray:
        launch_tray(args)
    else:
        try:
            main_cli(args)
        except KeyboardInterrupt:
            print("\nExiting LinWisp. Goodbye!")
            exit(0)
        except Exception as e:
            print(f"An error occurred: {e}")
            if args.gui:
                subprocess.run(["zenity", "--error", "--text", f"An error occurred: {e}"], shell=True)
            exit(1)