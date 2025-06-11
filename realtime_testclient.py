
#!/usr/bin/env python3
"""Test client for OpenAI Realtime Proxy.

Features:
- Send WAV (PCM16 LE, mono, 16 kHz) audio to the WebSocket endpoint and receive text → saves to .txt.
- Send a text prompt to the WebSocket endpoint and receive streamed PCM16 audio → saves to .wav.

Usage examples
--------------
# 1. Audio → Text
python realtime_test_client.py --mode audio --input angry_sample.wav --output transcript.txt

# 2. Text → Audio
python realtime_test_client.py --mode text --input \"I'm feeling overwhelmed, can you help?\" --output response.wav

# Optional flags
--url ws://localhost:8080/v1/realtime   # Change if server is remote
--sample-rate 16000                     # Audio sample‑rate (only when mode=text)

Dependencies
------------
pip install websockets soundfile   # soundfile only required if you need format conversions

"""
import argparse
import asyncio
import base64
import json
import sys
import wave
from pathlib import Path

import websockets   # pip install websockets

DEFAULT_WS_URL = "ws://localhost:8081/v1/realtime"

# ---------- Helpers ----------------------------------------------------------
def read_wav_as_pcm16(path: Path) -> bytes:
    """Read a mono 16‑bit PCM WAV and return raw bytes."""
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError("WAV must be mono 16‑bit PCM")
        return w.readframes(w.getnframes())

def write_pcm16_as_wav(pcm: bytes, path: Path, sample_rate: int = 16000):
    """Write raw PCM16 data to a WAV container (mono)."""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)

# ---------- Main client ------------------------------------------------------
async def audio_to_text(ws, audio_bytes: bytes, txt_path: Path):
    # 1) send audio buffer
    await ws.send(json.dumps({"type": "audio",
                              "audio": base64.b64encode(audio_bytes).decode()}))
    # 2) commit & request response
    await ws.send(json.dumps({"type": "audio_commit"}))

    # 3) collect streamed text
    transcript = []
    async for msg in ws:
        evt = json.loads(msg)
        if evt.get("type") == "text_response":
            transcript.append(evt.get("text", ""))
        elif evt.get("type") == "text_response_done":
            break

    txt_path.write_text("".join(transcript), encoding="utf‑8")
    print(f"✓ Transcript saved to {txt_path}")

async def text_to_audio(ws, text_prompt: str, wav_path: Path, sample_rate: int):
    # 1) send text message
    await ws.send(json.dumps({"type": "text", "text": text_prompt}))

    # 2) collect audio deltas
    pcm_chunks = []
    async for msg in ws:
        evt = json.loads(msg)
        if evt.get("type") == "audio_response":
            pcm_chunks.append(base64.b64decode(evt.get("audio")))
        elif evt.get("type") == "audio_response_done":
            break

    pcm_bytes = b"".join(pcm_chunks)
    write_pcm16_as_wav(pcm_bytes, wav_path, sample_rate)
    print(f"✓ Audio saved to {wav_path} ({len(pcm_bytes)/2/sample_rate:.2f}s)")

async def main():
    ap = argparse.ArgumentParser(description="Quick tester for OpenAI realtime proxy")
    ap.add_argument("--mode", choices=["audio", "text"], required=True,
                    help="audio: WAV→text, text: prompt→WAV")
    ap.add_argument("--input", required=True,
                    help="Path to WAV file (mode=audio) or text prompt (mode=text)")
    ap.add_argument("--output", required=True,
                    help="Path to save .txt (audio mode) or .wav (text mode)")
    ap.add_argument("--url", default=DEFAULT_WS_URL,
                    help=f"WebSocket endpoint (default {DEFAULT_WS_URL})")
    ap.add_argument("--sample-rate", type=int, default=16000,
                    help="Sample‑rate for generated WAV (mode=text)")
    args = ap.parse_args()

    async with websockets.connect(args.url) as ws:
        if args.mode == "audio":
            wav_path = Path(args.input)
            if not wav_path.exists():
                sys.exit(f"Audio file {wav_path} not found")
            audio_bytes = read_wav_as_pcm16(wav_path)
            await audio_to_text(ws, audio_bytes, Path(args.output))
        else:
            await text_to_audio(ws, args.input, Path(args.output), args.sample_rate)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user")
