"""
Tests for subtitles formatting logic with English, Hindi, and Bengali.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from subtitles import (
    format_srt_timestamp,
    format_display_timestamp,
    generate_srt,
    group_speaker_segments,
    generate_diarized_text,
)


def test_srt_timestamp():
    assert format_srt_timestamp(0.0) == "00:00:00,000"
    assert format_srt_timestamp(1.234) == "00:00:01,234"
    assert format_srt_timestamp(65.5) == "00:01:05,500"
    assert format_srt_timestamp(3665.12) == "01:01:05,120"
    print("✓ test_srt_timestamp passed")


def test_hindi_bengali_srt():
    mock_words = [
        {"text": "नमस्ते", "start": 0.1, "end": 0.6, "type": "word", "speaker_id": "speaker_0"},
        {"text": " ", "start": 0.6, "end": 0.7, "type": "spacing", "speaker_id": "speaker_0"},
        {"text": "दोस्तों।", "start": 0.7, "end": 1.2, "type": "word", "speaker_id": "speaker_0"},
        {"text": "आज", "start": 1.5, "end": 1.9, "type": "word", "speaker_id": "speaker_0"},
        {"text": "हम", "start": 1.9, "end": 2.2, "type": "word", "speaker_id": "speaker_0"},
        {"text": "हिंदी", "start": 2.2, "end": 2.7, "type": "word", "speaker_id": "speaker_0"},
        {"text": "सीखेंगे।", "start": 2.7, "end": 3.4, "type": "word", "speaker_id": "speaker_0"},
        # Bengali phrase with different speaker
        {"text": "কেমন", "start": 4.0, "end": 4.5, "type": "word", "speaker_id": "speaker_1"},
        {"text": "আছেন", "start": 4.5, "end": 5.0, "type": "word", "speaker_id": "speaker_1"},
        {"text": "সবাই?", "start": 5.0, "end": 5.5, "type": "word", "speaker_id": "speaker_1"},
    ]

    srt_out = generate_srt(mock_words)
    print("SRT output:\n" + srt_out)

    assert "नमस्ते दोस्तों।" in srt_out
    assert "কেমন আছেন সবাই?" in srt_out
    assert "00:00:00,100 --> 00:00:01,200" in srt_out
    print("✓ test_hindi_bengali_srt passed")


def test_speaker_segments():
    mock_words = [
        {"text": "Hello", "start": 0.0, "end": 0.5, "type": "word", "speaker_id": "speaker_0"},
        {"text": "world", "start": 0.5, "end": 1.0, "type": "word", "speaker_id": "speaker_0"},
        {"text": "Hi", "start": 1.2, "end": 1.5, "type": "word", "speaker_id": "speaker_1"},
        {"text": "there", "start": 1.5, "end": 2.0, "type": "word", "speaker_id": "speaker_1"},
    ]
    segments = group_speaker_segments(mock_words)
    assert len(segments) == 2
    assert segments[0]["speaker"] == "Speaker 1"
    assert segments[0]["text"] == "Hello world"
    assert segments[1]["speaker"] == "Speaker 2"
    assert segments[1]["text"] == "Hi there"

    diarized_text = generate_diarized_text(segments)
    assert "Speaker 1:" in diarized_text
    assert "Speaker 2:" in diarized_text
    print("✓ test_speaker_segments passed")


if __name__ == "__main__":
    test_srt_timestamp()
    test_hindi_bengali_srt()
    test_speaker_segments()
    print("All tests passed successfully!")
