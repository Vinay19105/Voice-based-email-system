Voice E-Mail System

A hands-free email assistant for Gmail. Control it entirely by voice (or by typing) to log in, send emails, and have your inbox read aloud — with speaker verification, multilingual support, and a desktop GUI.

✨ Features
Voice or typing input – switch between the two at any time ("switch to typing" / "switch to voice") or with the GUI buttons.
Wake word + speaker verification – say "start system"; if you registered your voice, only your voice unlocks the system (Resemblyzer voiceprint matching).
Online + offline speech recognition – Google Speech Recognition first, automatic fallback to offline Vosk (English).
Multilingual – speak and listen in 16 languages (see below). Output is translated and spoken with gTTS.
Send email – recipient, subject, body, and optional file attachments via Gmail SMTP.
Read email – unread, previously read, or all messages (latest 10), read aloud and shown in the GUI. Uses BODY.PEEK, so reading doesn't change unread status.
Contact book – new recipients are saved to contacts.json and reused by name.
Desktop GUI – dark-themed CustomTkinter dashboard with live transcript, inbox panel, message viewer, contacts, and status indicators.
📁 Project Structure
.
├── run.py                        # Entry point: starts voice engine thread + GUI
├── voice_email_system.py         # Voice engine (speech, wake word, email logic)
├── gui.py                        # CustomTkinter GUI
├── bridge.py                     # Thread-safe queues shared by engine and GUI
├── contacts.json                 # Saved name -> email contacts
├── history.json                  # Reserved for history (currently unused)
├── requirements.txt              # Python dependencies
└── vosk-model-small-en-us-0.15/  # Offline Vosk English model (folder)
How it fits together

run.py launches the voice engine in a background thread and the GUI in the main thread. They communicate through three queues defined in bridge.py:

Queue	Direction	Purpose
GUI_LOG_QUEUE	engine → GUI	Transcript lines shown in the GUI
GUI_COMMAND_QUEUE	engine ↔ GUI	Structured events (mode change, login, inbox list, status…)
INPUT_QUEUE	GUI → engine	Text typed in the GUI while in typing mode
🔧 Requirements
Python 3.8 – 3.10 recommended (some pinned packages, e.g. googletrans==4.0.0-rc1 and playsound==1.2.2, are fragile on newer versions)
A working microphone and speakers
A Gmail account with 2-Step Verification enabled and an App Password (regular passwords won't work)
Internet access for Google speech recognition, translation, and gTTS (English offline mode works without it)
🚀 Installation
Clone / download the project and open a terminal in its folder.
(Recommended) create a virtual environment
bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
Install dependencies
bash
   pip install -r requirements.txt

PyAudio troubleshooting

Windows: if pip install pyaudio fails, use pip install pipwin && pipwin install pyaudio.
macOS: brew install portaudio then pip install pyaudio.
Linux: sudo apt install portaudio19-dev python3-pyaudio then pip install pyaudio.
Download the Vosk model Get vosk-model-small-en-us-0.15 from https://alphacephei.com/vosk/models, unzip it, and place the folder in the project root (next to run.py). The path is set by VOSK_MODEL_PATH in voice_email_system.py.
Create a Gmail App Password Google Account → Security → 2-Step Verification → App passwords → generate a 16-character password. You'll speak or type this at login.
▶️ Running
bash
python run.py

The assistant will walk you through setup:

Choose input mode (voice or typing)
Choose a language (or say default for English)
Optionally register your voice (speak for ~5 seconds)
Say "start system" to unlock
Log in with your Gmail address and app password
Give commands
🗣️ Voice Commands
Say	Action
send email, compose email, write email	Compose and send a message (with optional attachment)
read email, check inbox, unread email, new email	Read unread emails
previous email, old email, seen email	Read previously read emails
all email, entire inbox	Read all emails
switch to voice / switch to typing	Change input mode
change language to <language>	Change spoken/recognized language
login / sign in	Log in again
logout / sign out	Log out
exit, shutdown, close system	Quit the program

💡 For email addresses, passwords, and file paths, typing mode is much more reliable than dictation. The assistant will suggest this when adding attachments.

Supported languages

English, Hindi, Spanish, French, German, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Chinese, Japanese, Arabic, Portuguese, Russian.

Offline (Vosk) recognition is English only. Other languages require an internet connection.

🖥️ GUI Overview
Header – status dot (idle / listening / speaking), logged-in badge, mode badge, language badge, and Voice / Typing buttons
Left panel – inbox list for the current scope
Center panel – live transcript, opened email, and a text box for typing mode
Right panel – contacts and session info
⚙️ Configuration

Edit the constants near the top of voice_email_system.py:

Setting	Default	Description
VOSK_MODEL_PATH	vosk-model-small-en-us-0.15	Path to the offline model
SAMPLE_RATE	16000	Audio sample rate (Hz)
FRAME_SIZE	512	Audio frame size
SPEAKER_MATCH_THRESHOLD	0.72	Voiceprint similarity needed to unlock (raise = stricter)
WAKE_BUFFER_SECONDS	2.5	Audio window used for speaker verification
🛠️ Troubleshooting
Problem	Fix
Login failed	Use a Gmail App Password, not your normal password. Make sure IMAP is enabled in Gmail settings.
Voice not recognized at wake word	Re-register your voice in a quiet room, or lower SPEAKER_MATCH_THRESHOLD slightly (e.g. 0.65). Watch the [speaker check] similarity value in the console.
Model / Vosk path error	Confirm the model folder sits next to run.py and the name matches VOSK_MODEL_PATH.
No microphone / PyAudio errors	Check OS microphone permissions and that no other app is using the mic.
Non-English speech doesn't play	gTTS needs internet; without it, the system falls back to the local English voice.
googletrans errors	Keep the pinned version 4.0.0-rc1; translation failures fall back to untranslated English text.
🔒 Security Notes
Your email and app password are held in memory only for the session; they are not written to disk.
contacts.json stores contact emails in plain text.
Use an App Password (revocable) rather than your main Google password, and revoke it if the machine is shared.
Voice verification is a convenience feature, not strong authentication.
📌 Known Limitations
Gmail only (hard-coded smtp.gmail.com / imap.gmail.com).
Inbox reading is capped at the 10 most recent messages per request; only the first 500 characters of a body are spoken.
Only plain-text email bodies are read aloud (HTML-only emails may be skipped).
Contact names are stored exactly as recognized by speech, so entries may need occasional cleanup in contacts.json.
🧰 Tech Stack

Python · Vosk · SpeechRecognition · Resemblyzer · PyAudio · pyttsx3 · gTTS · googletrans · SciPy / NumPy · CustomTkinter · smtplib / imaplib
