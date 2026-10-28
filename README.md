# AuScribe 🎙️

[![GitHub Repository](https://img.shields.io/badge/GitHub-mdtauhid29%2Fauscribe-indigo?logo=github)](https://github.com/mdtauhid29/auscribe)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)

A lightweight, multilingual audio transcription tool built for **Android** and desktop using the **ElevenLabs Scribe API** (Free Tier: 10,000 credits/month).

Optimized for **English (`en`)**, **Hindi (`hi`)**, and **Bengali (`bn`)** with one-tap export to **TXT** and **SRT (subtitles)** and live credit token tracking.

---

## ✨ Features

- 📱 **Mobile-First Android PWA**: Designed for Android touchscreens. Supports **"Add to Home Screen"** to run full-screen like a native app.
- 🗣️ **3 Core Languages**:
  - 🇬🇧 **English (`en`)**
  - 🇮🇳 **हिन्दी / Hindi (`hi`)**
  - 🇧🇩 **বাংলা / Bengali (`bn`)**
  *Selecting your language directly avoids wasting token quota on auto-detection and optimizes transcription accuracy.*
- 📊 **Credit & Token Monitor**: Displays live remaining credits from your 10,000 monthly free tier allowance, reset countdown, and usage percentages.
- 📥 **Export to TXT & SRT**:
  - **.TXT**: Plain clean text or speaker-separated text.
  - **.SRT**: Standard subtitle format (`00:00:01,200 --> 00:00:04,500`) with support for Hindi/Bengali sentence terminators (`।`).
- 🎙️ **Microphone & File Upload**:
  - Live voice recording directly from Android microphone.
  - File picker supporting MP3, M4A, WAV, AAC, OGG, Opus, WebM, and AMR (WhatsApp voice notes).
- 👥 **Speaker Diarization**: Detects and labels different speakers (Speaker 1, Speaker 2).
- 📲 **Android Share Sheet**: Share transcripts directly to WhatsApp, Telegram, Google Keep, or Gmail with one tap.
- 💻 **Dual Mode**: Mobile-friendly Web UI + Terminal CLI tool.

---

## 🚀 Running on Android

You have 3 easy ways to run and use this on your Android phone:

### Method 1: Directly on Android via Termux (Recommended - Standalone)

Run the entire app directly on your Android phone without needing a computer:

1. Install [Termux from F-Droid](https://f-droid.org/en/packages/com.termux/) (free, open source).
2. Open Termux and install Python & Git:
   ```bash
   pkg update && pkg install python git -y
   ```
3. Clone the repository into Termux:
   ```bash
   git clone https://github.com/mdtauhid29/auscribe.git
   cd auscribe
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the server:
   ```bash
   python app.py
   ```
6. Open Chrome or Firefox on your Android phone and visit:
   ```
   http://localhost:5000
   ```
7. **Install as App**: Tap Chrome's menu (three dots) -> tap **"Add to Home screen"** or **"Install App"**. It will appear on your phone's home screen as a standalone Android app!

---

### Method 2: Free 24/7 Cloud Deployment (Zero Setup on Phone)

Deploy it once to a free host like **Render**, **Railway**, or **Hugging Face Spaces**:

1. Push this folder to your GitHub repository.
2. In [Render.com](https://render.com) (or Railway):
   - Create a **New Web Service**.
   - Connect your GitHub repository.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py --port $PORT`
   - Add Environment Variable: `ELEVENLABS_API_KEY = your_key_here`
3. Open your custom URL on your Android phone (`https://your-app.onrender.com`).
4. Tap **"Add to Home screen"** in Chrome on Android. You now have a working Android app accessible anywhere!

---

### Method 3: Run on PC / Laptop & Access via Android over Wi-Fi

1. Install dependencies on your PC:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python app.py --host 0.0.0.0 --port 5000
   ```
3. Find your PC's local IP address (`ip a` on Linux or `ipconfig` on Windows, e.g. `192.168.1.15`).
4. On your Android phone connected to the same Wi-Fi, open Chrome and navigate to:
   ```
   http://192.168.1.15:5000
   ```

---

## 🔑 ElevenLabs API Key Setup

1. Sign up for a free account at [ElevenLabs.io](https://elevenlabs.io).
2. Go to **Profile** -> **API Keys** -> **Create API Key**.
3. You can set the key in either of two ways:
   - **In the UI**: Open the app on Android, tap the ⚙️ **Settings** icon, paste your key, and tap Save.
   - **In `.env`**: Copy `.env.example` to `.env` and fill in:
     ```env
     ELEVENLABS_API_KEY=sk_...
     ```

---

## 💻 CLI Usage (Terminal Mode)

You can also transcribe audio directly from the command line:

```bash
# Check remaining credits
python cli.py --credits

# Transcribe Hindi audio and export TXT & SRT
python cli.py -f voice_note.mp3 -l hi

# Transcribe Bengali audio with speaker diarization
python cli.py -f interview.m4a -l bn -d

# Transcribe English audio with custom output name
python cli.py -f meeting.wav -l en -o meeting_notes
```

### CLI Options:
| Flag | Description | Default |
|---|---|---|
| `-f, --file` | Path to audio file (`.mp3`, `.wav`, `.m4a`, etc.) | Required |
| `-l, --lang` | Target language: `en` (English), `hi` (Hindi), `bn` (Bengali) | `en` |
| `-d, --diarize` | Enable speaker identification (`Speaker 1`, `Speaker 2`) | `false` |
| `-o, --output` | Output prefix for `.txt` and `.srt` files | Audio filename |
| `-c, --credits`| View remaining ElevenLabs credit tokens | - |
| `-k, --key` | ElevenLabs API key (or set in `.env`) | - |

---

## 📁 Project Structure

```
auscribe/
├── app.py                 # Flask server & ElevenLabs API proxy
├── cli.py                 # Terminal CLI transcriber
├── subtitles.py           # SRT & diarized text formatting engine
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── static/
│   ├── manifest.json      # Android PWA Web App Manifest
│   ├── sw.js              # Service worker for offline caching & installability
│   └── icons/             # App icons (SVG, 192px, 512px)
├── templates/
│   └── index.html         # Mobile-first Android responsive UI
└── tests/
    ├── test_subtitles.py  # SRT generation unit tests
    └── test_app.py        # API endpoint tests
```

---

## 🧪 Running Tests

```bash
python -m unittest discover tests
```
