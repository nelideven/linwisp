'''
    LinWisp: A simple AI assistant for Linux using Google Gemini and OpenAI Whisper.
    This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/.
'''

import os
import json
import re
import tomli
import tomli_w
import subprocess

CONFIG_PATH = "config.toml"
API_KEY_PATH = "api_key"

def load_config(path=CONFIG_PATH):
    if not os.path.exists(path):
        default = {"model": "gemini-2.0-flash", "gui": False}
        save_config(default, path)
    with open(path, "rb") as f:
        return tomli.load(f)

def save_config(data, path=CONFIG_PATH):
    with open(path, "wb") as f:
        f.write(tomli_w.dumps(data).encode("utf-8"))

def load_api_key(path=API_KEY_PATH):
    if not os.path.exists(path):
        return ""
    with open(path, "r") as f:
        return f.read().strip()

def save_api_key(key, path=API_KEY_PATH):
    with open(path, "w") as f:
        f.write(key.strip())

def extract_text(gemini_output):
    try:
        response = json.loads(gemini_output)
        text = response["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        return text
    except Exception as e:
        return f"Error extracting response: {e}"

def ask_ai(prompt, api_key, model="gemini-2.0-flash"):
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    })
    cmd = [
        "curl",
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        "-H", "Content-Type: application/json",
        "-X", "POST",
        "-d", payload
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate()
    if proc.returncode == 0:
        return extract_text(stdout)
    else:
        raise RuntimeError(stderr.strip())