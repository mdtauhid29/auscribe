#!/usr/bin/env python3
"""
AuScribe - Audio Transcription Tool powered by ElevenLabs Scribe API.
Optimized for Android & Web. Supports English (en), Hindi (hi), and Bengali (bn).
"""

import os
import io
import time
import json
import logging
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from dotenv import load_dotenv

from subtitles import (
    generate_srt,
    group_speaker_segments,
    generate_diarized_text,
    format_display_timestamp
)

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "scribe_v2"

# Allowed languages per user requirements
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "flag": "🇬🇧"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
    "bn": {"name": "Bengali", "native": "বাংলা", "flag": "🇧🇩"},
}


def get_api_key(client_req) -> Optional[str]:
    """
    Retrieve API key from either:
    1. Client custom header 'X-ElevenLabs-Key' (set in Android UI settings)
    2. Server environment variable ELEVENLABS_API_KEY
    """
    key = client_req.headers.get("X-ElevenLabs-Key")
    if key and key.strip():
        return key.strip()
    return os.getenv("ELEVENLABS_API_KEY", "").strip() or None


@app.route("/")
def index():
    has_server_key = bool(os.getenv("ELEVENLABS_API_KEY", "").strip())
    return render_template("index.html", has_server_key=has_server_key, languages=SUPPORTED_LANGUAGES)


@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/api/health", methods=["GET"])
def health_check():
    has_key = bool(os.getenv("ELEVENLABS_API_KEY", "").strip())
    return jsonify({
        "status": "online",
        "app": "AuScribe",
        "version": "1.0.0",
        "server_api_key_configured": has_key,
        "supported_languages": list(SUPPORTED_LANGUAGES.keys())
    })


@app.route("/api/subscription", methods=["GET"])
def get_subscription():
    """
    Fetch user's ElevenLabs subscription & credit token usage.
    Returns: character_limit (e.g. 10000), character_count (used), remaining_credits, reset date.
    """
    api_key = get_api_key(request)
    if not api_key:
        return jsonify({
            "error": "ElevenLabs API key missing. Please enter your API key in settings or set ELEVENLABS_API_KEY."
        }), 401

    try:
        resp = requests.get(
            f"{ELEVENLABS_BASE_URL}/user/subscription",
            headers={"xi-api-key": api_key},
            timeout=10
        )
        if resp.status_code != 200:
            error_msg = resp.text
            try:
                error_json = resp.json()
                error_msg = error_json.get("detail", {}).get("message") or error_json.get("message") or resp.text
            except Exception:
                pass
            return jsonify({"error": f"ElevenLabs API Error ({resp.status_code}): {error_msg}"}), resp.status_code

        sub_data = resp.json()
        char_limit = sub_data.get("character_limit", 10000)
        char_count = sub_data.get("character_count", 0)
        remaining = max(0, char_limit - char_count)
        reset_unix = sub_data.get("next_character_count_reset_unix", 0)
        tier = sub_data.get("tier", "free")

        return jsonify({
            "tier": tier,
            "character_limit": char_limit,
            "character_count": char_count,
            "remaining_credits": remaining,
            "used_percentage": round((char_count / char_limit) * 100, 1) if char_limit else 0,
            "next_reset_unix": reset_unix,
            "status": sub_data.get("status", "active"),
        })

    except requests.RequestException as e:
        logging.error(f"Subscription request failed: {e}")
        return jsonify({"error": f"Network error connecting to ElevenLabs: {str(e)}"}), 502


@app.route("/api/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Transcribe audio using ElevenLabs Scribe API (scribe_v2).
    Accepts:
      - audio: file multipart upload
      - language_code: 'en' | 'hi' | 'bn' (User chosen to save tokens & boost accuracy)
      - diarize: 'true' | 'false' (optional)
      - tag_audio_events: 'true' | 'false' (optional)
    """
    api_key = get_api_key(request)
    if not api_key:
        return jsonify({
            "error": "API Key required. Please provide your ElevenLabs API key in settings."
        }), 401

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided in request."}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "Empty audio file uploaded."}), 400

    # User-selected language code (en, hi, bn)
    lang_code = request.form.get("language_code", "en").lower().strip()
    if lang_code not in SUPPORTED_LANGUAGES:
        return jsonify({
            "error": f"Invalid language code '{lang_code}'. Supported languages are: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        }), 400

    diarize = request.form.get("diarize", "false").lower() in ("true", "1", "yes")
    tag_events = request.form.get("tag_audio_events", "true").lower() in ("true", "1", "yes")

    logging.info(f"Transcribing '{audio_file.filename}' with lang='{lang_code}', diarize={diarize}")

    try:
        # Prepare multipart data
        files = {
            "file": (audio_file.filename or "recording.webm", audio_file.stream, audio_file.mimetype or "audio/mpeg")
        }
        data = {
            "model_id": DEFAULT_MODEL,
            "language_code": lang_code,
            "diarize": "true" if diarize else "false",
            "tag_audio_events": "true" if tag_events else "false",
            "timestamps_granularity": "word"
        }

        # Send request to ElevenLabs Scribe API
        response = requests.post(
            f"{ELEVENLABS_BASE_URL}/speech-to-text",
            headers={"xi-api-key": api_key},
            data=data,
            files=files,
            timeout=180
        )

        if response.status_code != 200:
            error_msg = response.text
            try:
                err_json = response.json()
                error_msg = err_json.get("detail", {}).get("message") or err_json.get("message") or response.text
            except Exception:
                pass
            logging.error(f"ElevenLabs transcription error {response.status_code}: {error_msg}")
            return jsonify({"error": f"Transcription failed ({response.status_code}): {error_msg}"}), response.status_code

        res_data = response.json()

        # Extract words & full text
        full_text = res_data.get("text", "").strip()
        words = res_data.get("words", [])
        detected_lang = res_data.get("language_code", lang_code)
        duration_secs = res_data.get("audio_duration_secs", 0)

        # Generate SRT format
        srt_content = generate_srt(words, full_text=full_text)

        # Generate speaker segments for rich UI display
        speaker_segments = group_speaker_segments(words, full_text=full_text)
        diarized_text = generate_diarized_text(speaker_segments)

        # Fetch updated subscription info if available
        sub_info = None
        try:
            sub_res = requests.get(
                f"{ELEVENLABS_BASE_URL}/user/subscription",
                headers={"xi-api-key": api_key},
                timeout=5
            )
            if sub_res.status_code == 200:
                sub_data = sub_res.json()
                char_limit = sub_data.get("character_limit", 10000)
                char_count = sub_data.get("character_count", 0)
                sub_info = {
                    "remaining_credits": max(0, char_limit - char_count),
                    "character_count": char_count,
                    "character_limit": char_limit,
                    "used_percentage": round((char_count / char_limit) * 100, 1) if char_limit else 0
                }
        except Exception as e:
            logging.warning(f"Failed to refresh subscription after transcribe: {e}")

        return jsonify({
            "success": True,
            "text": full_text,
            "srt": srt_content,
            "diarized_text": diarized_text,
            "segments": speaker_segments,
            "audio_duration_secs": duration_secs,
            "duration_formatted": format_display_timestamp(duration_secs),
            "language_code": detected_lang,
            "word_count": len([w for w in words if w.get("type", "word") == "word"]),
            "subscription": sub_info
        })

    except requests.Timeout:
        return jsonify({"error": "Request timed out while transcribing audio. Please try with a shorter clip."}), 504
    except requests.RequestException as e:
        logging.error(f"Network error during transcription: {e}")
        return jsonify({"error": f"Network error connecting to ElevenLabs: {str(e)}"}), 502
    except Exception as e:
        logging.exception("Unexpected error in transcription handler")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AuScribe Audio Transcription Server")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="Host IP (0.0.0.0 for LAN/Android access)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)), help="Port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print(" 🎙️  AuScribe Server Running!")
    print(f" • Local Access:    http://127.0.0.1:{args.port}")
    print(f" • Android/Network: http://<your-device-ip>:{args.port}")
    print("=" * 55 + "\n")

    app.run(host=args.host, port=args.port, debug=args.debug)
