
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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging

import websockets   # pip install websockets

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)
DEFAULT_WS_URL = "ws://0.0.0.0/v1/realtime"

# ------------------------- Helpers ---------------------------
def read_wav_as_pcm16(path: Path) -> bytes:
    """Read a mono 16‑bit PCM WAV and return raw bytes."""
    with wave.open(str(path), "rb") as w:
        if w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError("WAV must be mono 16‑bit PCM")
        logger.info("Loaded WAV file '%s' (%d bytes)", path, len(data))
        return w.readframes(w.getnframes())

def write_pcm16_as_wav(pcm: bytes, path: Path, sample_rate: int = 16000):
    """Write raw PCM16 data to a WAV container (mono)."""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
        logger.info("Wrote WAV file '%s' (%.2f seconds)", path, len(pcm) / 2 / sample_rate)

# ---------- Main client ------------------------------------------------------
async def audio_to_text(ws, audio_bytes: bytes, txt_path: Path):
    payload = {"type": "audio", "audio": base64.b64encode(audio_bytes).decode()}
    logger.info("Sending request to server: %s", payload)
    # 1) send audio buffer
    await ws.send(json.dumps({"type": "audio",
                              "audio": base64.b64encode(audio_bytes).decode()}))
    # 2) commit & request response
    commit = {"type": "audio_commit"}
    logger.info("Sending commit request: %s", commit)
    # 2) commit & request response
    await ws.send(json.dumps({"type": "audio_commit"}))

    # 3) collect streamed text
    transcript = []
    async for msg in ws:
        logger.info("Received raw message: %s", msg)
        evt = json.loads(msg)
        typ = evt.get("type")
        if evt.get("type") == "text_response":
            text_chunk = evt.get("text", "")
            logger.info("Text chunk received: '%s'", text_chunk)
            transcript.append(evt.get("text", ""))
        elif evt.get("type") == "text_response_done":
            logger.info("End of text response")
            break

    txt_path.write_text("".join(transcript), encoding="utf‑8")
    logger.info("Transcript saved to %s", txt_path)

async def text_to_audio(ws, text_prompt: str, wav_path: Path, sample_rate: int):
    # 1) send text message
    payload = {"type": "text", "text": text_prompt}
    logger.info("Sending request to server: %s", payload)
    await ws.send(json.dumps(payload))

    # 2) collect audio deltas
    pcm_chunks = []
    async for msg in ws:
        logger.info("Received raw message: %s", msg)
        evt = json.loads(msg)
        typ = evt.get("type")
        if evt.get("type") == "audio_response":
            audio_data = base64.b64decode(evt.get("audio"))
            logger.info("Audio chunk received (%d bytes)", len(audio_data))
            pcm_chunks.append(base64.b64decode(evt.get("audio")))
        elif evt.get("type") == "audio_response_done":
            logger.info("End of audio response")
            break

    pcm_bytes = b"".join(pcm_chunks)
    write_pcm16_as_wav(pcm_bytes, wav_path, sample_rate)
    logger.info("Audio saved to %s", wav_path)

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

    logger.info("Connecting to WebSocket URL: %s", args.url)


    async with websockets.connect(args.url) as ws:
        logger.info("WebSocket connection established")
        if args.mode == "audio":
            wav_path = Path(args.input)
            if not wav_path.exists():
                logger.error("Audio file %s not found", wav_path)
                sys.exit(1)
            audio_bytes = read_wav_as_pcm16(wav_path)
            await audio_to_text(ws, audio_bytes, Path(args.output))
        else:
            await text_to_audio(ws, args.input, Path(args.output), args.sample_rate)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
