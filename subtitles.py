"""
Subtitle and text formatting utilities for ElevenLabs Scribe transcriptions.
Supports English, Hindi, and Bengali with punctuation awareness (including '।').
"""

import math
from typing import List, Dict, Any, Optional


def format_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_display_timestamp(seconds: float) -> str:
    """Convert seconds to user-friendly MM:SS or HH:MM:SS format"""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


# Punctuation marks indicating sentence boundaries in English, Hindi, and Bengali
SENTENCE_ENDINGS = {".", "!", "?", "।", "॥", "…", "\n"}


def generate_srt(
    words: Optional[List[Dict[str, Any]]],
    full_text: Optional[str] = None,
    max_words_per_cue: int = 8,
    max_duration_secs: float = 4.0,
    max_gap_secs: float = 1.0,
) -> str:
    """
    Generate standard SubRip (.srt) subtitles from ElevenLabs word-level transcription.
    Handles English, Hindi, and Bengali sentence terminations and speaker transitions.
    """
    if not words:
        if full_text:
            return _generate_srt_from_text(full_text)
        return ""

    # Filter out pure spacing tokens to clean up token stream, but keep punctuation & events
    cleaned_tokens = []
    for w in words:
        w_type = w.get("type", "word")
        text = w.get("text", "")
        # If type is spacing and text is whitespace, skip it as separate token
        if w_type == "spacing" or not text.strip():
            continue
        cleaned_tokens.append(w)

    if not cleaned_tokens:
        if full_text:
            return _generate_srt_from_text(full_text)
        return ""

    cues = []
    current_cue_words = []
    current_cue_start = None
    current_speaker = None

    def flush_cue():
        nonlocal current_cue_words, current_cue_start, current_speaker
        if not current_cue_words:
            return
        cue_start = current_cue_start if current_cue_start is not None else current_cue_words[0].get("start", 0)
        cue_end = current_cue_words[-1].get("end", cue_start + 1.0)
        
        # Ensure minimum duration for readability
        if cue_end <= cue_start:
            cue_end = cue_start + 1.0
            
        cue_text = " ".join(t.get("text", "").strip() for t in current_cue_words if t.get("text", "").strip())
        if cue_text:
            cues.append({
                "start": cue_start,
                "end": cue_end,
                "text": cue_text,
                "speaker": current_speaker
            })
        current_cue_words = []
        current_cue_start = None
        current_speaker = None

    for i, token in enumerate(cleaned_tokens):
        token_text = token.get("text", "").strip()
        if not token_text:
            continue

        token_start = token.get("start", 0.0)
        token_end = token.get("end", token_start + 0.3)
        token_speaker = token.get("speaker_id")

        if not current_cue_words:
            current_cue_start = token_start
            current_speaker = token_speaker
            current_cue_words.append(token)
        else:
            prev_token = current_cue_words[-1]
            prev_end = prev_token.get("end", token_start)
            time_gap = token_start - prev_end
            cue_duration = token_end - (current_cue_start or token_start)

            # Check break conditions:
            # 1. Speaker change
            speaker_changed = (token_speaker != current_speaker and token_speaker is not None and current_speaker is not None)
            # 2. Previous token ended with sentence punctuation (. ? ! ।)
            prev_text = prev_token.get("text", "").strip()
            ended_sentence = any(prev_text.endswith(p) for p in SENTENCE_ENDINGS)
            # 3. Large pause/silence gap
            large_gap = time_gap > max_gap_secs
            # 4. Exceeded max words or duration
            too_long = len(current_cue_words) >= max_words_per_cue or cue_duration >= max_duration_secs

            if speaker_changed or ended_sentence or large_gap or too_long:
                flush_cue()
                current_cue_start = token_start
                current_speaker = token_speaker
                current_cue_words.append(token)
            else:
                current_cue_words.append(token)

    flush_cue()

    # Format into standard SRT string
    srt_lines = []
    for idx, cue in enumerate(cues, 1):
        start_str = format_srt_timestamp(cue["start"])
        end_str = format_srt_timestamp(cue["end"])
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(cue["text"])
        srt_lines.append("")  # Blank line separator

    return "\n".join(srt_lines).strip() + "\n"


def _generate_srt_from_text(full_text: str, words_per_cue: int = 8, sec_per_word: float = 0.4) -> str:
    """Fallback SRT generation when only full text is available without word timestamps."""
    words = full_text.split()
    if not words:
        return ""
    
    cues = []
    current_time = 0.0
    for i in range(0, len(words), words_per_cue):
        chunk = words[i:i + words_per_cue]
        duration = max(1.5, len(chunk) * sec_per_word)
        start_str = format_srt_timestamp(current_time)
        end_str = format_srt_timestamp(current_time + duration)
        cue_idx = (i // words_per_cue) + 1
        cues.append(f"{cue_idx}\n{start_str} --> {end_str}\n{' '.join(chunk)}\n")
        current_time += duration + 0.2
    return "\n".join(cues)


def group_speaker_segments(
    words: Optional[List[Dict[str, Any]]],
    full_text: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Groups words into readable diarized segments by speaker with timestamps.
    """
    if not words:
        return [{
            "speaker": "Speaker 1",
            "speaker_id": "speaker_0",
            "start": 0.0,
            "end": 0.0,
            "start_formatted": "00:00",
            "text": full_text or ""
        }]

    # Human-readable speaker names map (speaker_0 -> Speaker 1, etc.)
    speaker_map: Dict[str, str] = {}
    
    def get_speaker_label(spk_id: Optional[str]) -> str:
        if not spk_id:
            return "Speaker 1"
        if spk_id not in speaker_map:
            idx = len(speaker_map) + 1
            speaker_map[spk_id] = f"Speaker {idx}"
        return speaker_map[spk_id]

    segments: List[Dict[str, Any]] = []
    current_speaker_id: Optional[str] = None
    current_words: List[str] = []
    current_start: float = 0.0
    current_end: float = 0.0

    def flush_segment():
        nonlocal current_speaker_id, current_words, current_start, current_end
        if not current_words:
            return
        text_joined = " ".join(current_words).strip()
        if text_joined:
            segments.append({
                "speaker": get_speaker_label(current_speaker_id),
                "speaker_id": current_speaker_id or "speaker_0",
                "start": round(current_start, 2),
                "end": round(current_end, 2),
                "start_formatted": format_display_timestamp(current_start),
                "end_formatted": format_display_timestamp(current_end),
                "text": text_joined
            })
        current_words = []

    for token in words:
        token_type = token.get("type", "word")
        token_text = token.get("text", "")
        if token_type == "spacing" or not token_text.strip():
            continue

        spk_id = token.get("speaker_id")
        start = token.get("start", 0.0)
        end = token.get("end", start + 0.3)

        if current_speaker_id is None:
            current_speaker_id = spk_id
            current_start = start
            current_end = end
            current_words.append(token_text.strip())
        elif spk_id != current_speaker_id:
            flush_segment()
            current_speaker_id = spk_id
            current_start = start
            current_end = end
            current_words.append(token_text.strip())
        else:
            current_words.append(token_text.strip())
            current_end = end

    flush_segment()

    if not segments and full_text:
        segments.append({
            "speaker": "Speaker 1",
            "speaker_id": "speaker_0",
            "start": 0.0,
            "end": 0.0,
            "start_formatted": "00:00",
            "end_formatted": "00:00",
            "text": full_text
        })

    return segments


def generate_diarized_text(segments: List[Dict[str, Any]]) -> str:
    """Format segments into clean text with speaker headings and timestamps."""
    lines = []
    for seg in segments:
        lines.append(f"[{seg['start_formatted']}] {seg['speaker']}:")
        lines.append(seg['text'])
        lines.append("")
    return "\n".join(lines).strip()
