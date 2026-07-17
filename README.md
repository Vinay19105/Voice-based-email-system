# Voice based email system

A voice-controlled email client for Gmail: login, send, and read email
by speaking, with a typing-mode fallback, offline speech recognition
(Vosk), and optional voice-based access control (Resemblyzer).

## Files

- `voice_email_system.py` — the voice engine (listening, speaking, login, send/read email)
- `bridge.py` — the queues connecting the engine to the GUI, and the event protocol they carry
- `gui.py` — a modern CustomTkinter dashboard: live listening/speaking indicator, mode + login
  badges, the actual inbox contents, the currently-open message, saved contacts, the last email
  sent, and a full transcript with a typing-mode input box
- `run.py` — entry point; starts the engine in a background thread and the GUI on the main thread
- `contacts.json` — created automatically the first time you send an email to a new name

### What the GUI shows

- **Header** — a status dot + line that turns amber while the engine is listening and teal while
  it's speaking, plus badges for the current mode (voice/typing) and login state, and buttons to
  force-switch modes
- **Inbox panel** (left) — every unread message fetched by "read email", with the currently open
  one highlighted
- **Open message** (center top) — sender, subject, and body of whatever was last read aloud
- **Transcript** (center bottom) — everything spoken and heard, plus a text box for typing
  commands directly
- **Engine state / Last sent / Contacts** (right) — a bigger listening/speaking readout, the most
  recent email you sent, and your saved contacts list

## Setup

1. Install Python 3.10 or 3.11 (Vosk and PyAudio wheels are most reliable on these versions).

2. Install system audio dependencies first, since `pyaudio` needs PortAudio:
   - macOS: `brew install portaudio`
   - Ubuntu/Debian: `sudo apt install portaudio19-dev python3-pyaudio`
   - Windows: usually installs cleanly via pip alone

3. Install Python packages:
   ```
   pip install -r requirements.txt
   ```
   This now includes `customtkinter`, which powers the GUI's modern look. Plain Tkinter
   (bundled with Python) is still the underlying toolkit, so no separate system install is needed
   for it — just the pip package.

4. Download a Vosk offline model and unzip it next to these files as
   `vosk-model-small-en-us-0.15` (get it from https://alphacephei.com/vosk/models —
   this is used as a fallback when Google's online recognizer is unavailable,
   and for the wake-word listener).

5. `gTTS`, `googletrans`, and Google's speech recognizer all need internet access — they're
   free, keyless web APIs, not local models. `playsound` is pinned to `1.2.2` in
   `requirements.txt`, since later 1.3.x releases have had packaging issues on some platforms.

6. Generate a Gmail **App Password** (not your normal password) at
   https://myaccount.google.com/apppasswords — this requires 2-Step
   Verification to be enabled on the account. Use the app password when
   the system asks for your password.

## Run

```
python run.py
```

This opens the GUI and starts the voice engine. Say "voice" or "typing"
when prompted to pick your input mode, then "start system" to pass the
wake-word check, then log in with your Gmail address and app password.

To run the voice engine without the GUI (console only):

```
python voice_email_system.py
```

## Voice commands

- `login` / `sign in`
- `send email` / `compose email` / `write email`
- `read unread email` / `new email` — unread messages only
- `read all email` / `entire inbox` — every message, read and unread
- `read previous email` / `old email` / `seen email` — only messages already marked read
- `read email` / `check inbox` (no qualifier) — defaults to unread, same as before
- `change language to <name>` / `switch language to <name>` — see supported languages below
- `logout` / `sign out`
- `switch to voice` / `switch to typing`
- `exit` / `shutdown` / `close system`

## Multilingual voice input & output

At startup, after choosing voice/typing mode, the system now asks which language you want
(`choose_language()`), and you can switch anytime by saying `change language to hindi` (or any
supported name). This affects both directions:

- **Input** — `listen()` passes the matching locale (e.g. `hi-IN`) to Google's speech recognizer,
  so it transcribes what you say in that language instead of assuming English.
- **Output** — `speak()` translates the system's response with `googletrans` and synthesizes it
  with `gTTS` in that language, playing it back with `playsound`. If `gTTS` can't reach the network
  or the language code fails, it falls back to the local `pyttsx3` voice in English so the system
  never goes silent.

Supported names right now: english, hindi, spanish, french, german, tamil, telugu, kannada,
malayalam, bengali, marathi, chinese, japanese, arabic, portuguese, russian — see `LANGUAGES` in
`voice_email_system.py` to add more (it just needs a Google speech-recognition locale and a
gTTS/`googletrans` language code).

Note: the offline Vosk fallback (used when there's no network) only understands English, since
`vosk-model-small-en-us-0.15` is an English acoustic model. Fully offline multilingual recognition
would need a separate Vosk model per language — ask if you want that wired in.

## What was actually wrong with voice authentication

Two separate bugs were compounding:

1. **Un-normalized audio.** Raw microphone bytes are 16-bit PCM in the range roughly
   ±32768. Resemblyzer expects a waveform normalized to **[-1, 1]** — the old code cast the
   int16 buffer straight to `float32` without dividing by 32768, so every embedding was
   computed on a wildly out-of-range signal. `pcm16_to_float_wav()` now does that conversion
   consistently everywhere, and `preprocess_wav()` is applied too (denoising, resampling, and
   silence trimming that Resemblyzer's own examples expect).

2. **Not enough audio to embed.** The wake-word listener was checking the speaker's identity on
   a single 512-sample frame — about **32 milliseconds** of audio. That's nowhere near enough
   signal for a voice embedding; it's a large part of why it "never recognized" the registered
   voice. `wake_word_listener()` now keeps a rolling ~2.5 second buffer of raw audio and runs the
   speaker check against that whole window once the wake phrase is detected, and
   `is_same_speaker()` bails out (returns False) if less than about a second of speech survives
   silence-trimming, rather than embedding near-silence and comparing it anyway.

The similarity threshold was also nudged from 0.75 to 0.72 — a reasonable middle ground once the
embeddings are actually being computed on valid audio; you may want to tune it after testing with
your own mic and voice.

## Reading unread vs previously-read vs all email

`read_email(scope)` now takes `"unseen"`, `"seen"`, or `"all"`, mapped straight to IMAP search
criteria (`UNSEEN`, `SEEN`, `ALL`). It also fetches with `BODY.PEEK[]` instead of `RFC822` — the
old fetch implicitly marked every unread message it touched as read, which meant "read unread
email" and "read previous email" would drift out of sync with what Gmail actually shows as
unread. `BODY.PEEK[]` reads the content without changing its read/unread flag on the server.

## Notes

- Credentials are kept in memory only (`EMAIL` / `PASSWORD` globals) for
  the life of the process — they are never written to disk. Still,
  Gmail app passwords should be treated as sensitive; revoke one at
  the link above if you're done testing.
- `record_voice_profile()` / `is_same_speaker()` add lightweight voice
  verification for the wake-word step. It's a similarity threshold on
  Resemblyzer embeddings, not a security-grade biometric check — don't
  rely on it as your only access control.
- Speech recognition tries Google's free online API first, then falls
  back to the offline Vosk model if that fails (no network, quota, etc).
