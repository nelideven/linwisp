# LinWisp
A simple AI assistant for Linux using Google Gemini and OpenAI Whisper. This tool is designed to be your AI companion, similar to Siri and Google Gemini in devices.

## Dependencies
System packages:<br>
Python 3 (3.9 or higher recommended)<br>
espeak (for text-to-speech)<br>
libportaudio2 (required by sounddevice)<br>
ffmpeg<br>
gir1.2-gtk-3.0<br>
gir1.2-appindicator3-0.1 OR gir1.2-ayatanaappindicator (depending on your distro)

Python packages:<br>
NumPy<br>
tomli & tomli_w<br>
openai-whisper<br>
sounddevice<br>
webrtcvad<br>
pycairo<br>
PyGObject

## How-to
Use:
1. Install the required packages (if already installed, you can ignore it),
2. Download the main.py and core.py and place it in the same folder,
3. Afterwards, you can either run it directly (python3 main.py) or place the tray (python3 main.py --tray).
