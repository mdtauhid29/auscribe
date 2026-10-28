#!/usr/bin/env python3
"""
AuScribe CLI - Command-Line Interface for ElevenLabs Scribe STT.
Transcribe audio files into TXT and SRT subtitles directly from the terminal (Termux / Linux / Mac / Windows).
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

from subtitles import (
    generate_srt,
    group_speaker_segments,
    generate_diarized_text,
    format_display_timestamp
)

load_dotenv()

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
SUPPORTED_LANGS = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "bn": "Bengali (বাংলা)"
}


def get_api_key(cli_key: str = None) -> str:
    key = cli_key or os.getenv("ELEVENLABS_API_KEY")
    if not key:
        print("\n❌ Error: ElevenLabs API Key not found.")
        print("Please provide it via --key YOUR_KEY or set ELEVENLABS_API_KEY in your .env file.")
        print("Get your free API key at: https://elevenlabs.io/app/settings/api-keys\n")
        sys.exit(1)
    return key.strip()


def check_subscription(api_key: str):
    """Check remaining credit tokens."""
    try:
        res = requests.get(
            f"{ELEVENLABS_BASE_URL}/user/subscription",
            headers={"xi-api-key": api_key},
            timeout=10
        )
        if res.status_code != 200:
            print(f"❌ Failed to fetch subscription: {res.status_code} - {res.text}")
            return
        data = res.json()
        limit = data.get("character_limit", 10000)
        used = data.get("character_count", 0)
        remaining = max(0, limit - used)
        tier = data.get("tier", "free")
        
        print("\n" + "=" * 45)
        print(" 📊 ElevenLabs Account & Credit Status")
        print("=" * 45)
        print(f" • Subscription Tier:  {tier.upper()}")
        print(f" • Total Limit:        {limit:,} characters/credits")
        print(f" • Characters Used:    {used:,} characters/credits")
        print(f" • Remaining Credits:  {remaining:,} credits")
        print(f" • Usage Percentage:   {(used / limit * 100):.1f}%")
        print("=" * 45 + "\n")
    except Exception as e:
        print(f"❌ Network error checking credits: {e}")


def transcribe_file(file_path: str, lang: str, diarize: bool, api_key: str, out_prefix: str = None):
    if not os.path.exists(file_path):
        print(f"❌ Audio file not found: {file_path}")
        sys.exit(1)

    lang = lang.lower().strip()
    if lang not in SUPPORTED_LANGS:
        print(f"❌ Invalid language '{lang}'. Choose from: {', '.join(SUPPORTED_LANGS.keys())}")
        sys.exit(1)

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"\n🎙️  AuScribe STT Processing")
    print(f" • Audio File:  {file_path} ({file_size_mb:.2f} MB)")
    print(f" • Language:    {SUPPORTED_LANGS[lang]} ({lang})")
    print(f" • Diarization: {'Enabled' if diarize else 'Disabled'}")
    print(" • Sending to ElevenLabs Scribe v2... (please wait)")

    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f)
        }
        data = {
            "model_id": "scribe_v2",
            "language_code": lang,
            "diarize": "true" if diarize else "false",
            "tag_audio_events": "true",
            "timestamps_granularity": "word"
        }

        try:
            res = requests.post(
                f"{ELEVENLABS_BASE_URL}/speech-to-text",
                headers={"xi-api-key": api_key},
                data=data,
                files=files,
                timeout=180
            )
            if res.status_code != 200:
                print(f"\n❌ Transcription API Error ({res.status_code}): {res.text}")
                sys.exit(1)

            res_json = res.json()
        except requests.RequestException as e:
            print(f"\n❌ Request failed: {e}")
            sys.exit(1)

    full_text = res_json.get("text", "").strip()
    words = res_json.get("words", [])
    duration_secs = res_json.get("audio_duration_secs", 0)

    # Generate SRT and Diarized text
    srt_text = generate_srt(words, full_text=full_text)
    segments = group_speaker_segments(words, full_text=full_text)
    diarized_txt = generate_diarized_text(segments)

    # Determine output file paths
    base_name = out_prefix or os.path.splitext(file_path)[0]
    txt_path = f"{base_name}.txt"
    srt_path = f"{base_name}.srt"

    # Write files
    with open(txt_path, "w", encoding="utf-8") as f_txt:
        f_txt.write(diarized_txt if diarize else full_text)

    with open(srt_path, "w", encoding="utf-8") as f_srt:
        f_srt.write(srt_text)

    print("\n" + "=" * 50)
    print(" ✅ Transcription Successful!")
    print("=" * 50)
    print(f" • Audio Duration:   {format_display_timestamp(duration_secs)} ({duration_secs:.1f}s)")
    print(f" • Plain Text File:  {txt_path}")
    print(f" • Subtitle File:    {srt_path}")
    print("=" * 50)
    print("\n--- Preview ---")
    preview = full_text[:280] + ("..." if len(full_text) > 280 else "")
    print(preview)
    print("----------------\n")


def main():
    parser = argparse.ArgumentParser(
        description="AuScribe - Audio Transcription CLI for ElevenLabs Scribe STT"
    )
    parser.add_argument("-f", "--file", help="Path to audio file (mp3, wav, m4a, ogg, etc.)")
    parser.add_argument(
        "-l", "--lang",
        choices=["en", "hi", "bn"],
        default="en",
        help="Target language: en (English), hi (Hindi), bn (Bengali)"
    )
    parser.add_argument("-d", "--diarize", action="store_true", help="Enable speaker diarization")
    parser.add_argument("-o", "--output", help="Output filename prefix (without extension)")
    parser.add_argument("-k", "--key", help="ElevenLabs API Key")
    parser.add_argument("-c", "--credits", action="store_true", help="Check remaining ElevenLabs credits")

    args = parser.parse_args()
    api_key = get_api_key(args.key)

    if args.credits:
        check_subscription(api_key)
        if not args.file:
            return

    if not args.file:
        parser.print_help()
        sys.exit(1)

    transcribe_file(args.file, args.lang, args.diarize, api_key, args.output)


if __name__ == "__main__":
    main()
