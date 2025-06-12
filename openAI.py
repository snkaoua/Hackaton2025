#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openAI.py  –  realtime GPT-4o (אם יש KEY)  ▲▼  או Edge-TTS + Google-STT מקומיים

pip install fastapi uvicorn websockets edge-tts SpeechRecognition pipwin
pipwin install pyaudio      # Windows בלבד ל-SpeechRecognition
"""

import asyncio, base64, json, os, logging, tempfile
from typing import Dict, Any

import websockets                             # משמש רק עם OpenAI-Key
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ─────────────── ייבוא הקבצים החדשים ────────────────
from tts import text_to_speech        # async text→MP3
from stt import speech_to_text        # file→text
# ─────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("rt-proxy")

app = FastAPI(title="Realtime Audio Proxy")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ═══════════════  עטיפות TTS/STT בסיס-64  ═══════════════
async def tts_mp3_b64(text: str) -> str:
    """text_to_speech → base64-MP3"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    await text_to_speech(text, out_path)      # הפונקציה מה-tts.py
    mp3_bytes = open(out_path, "rb").read()
    os.remove(out_path)
    return base64.b64encode(mp3_bytes).decode()

def stt_b64_to_text(b64_wav: str, lang="en-US") -> str:
    """base64-WAV → speech_to_text()"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(base64.b64decode(b64_wav)); tmp.flush()
        text = speech_to_text(tmp.name, lang=lang)
    os.remove(tmp.name)
    return text
# ═══════════════════════════════════════════════════════

def compute_stress(s: Dict[str, Any]) -> float:
    rage = s.get("rage_probability", 0)/100
    hr   = s.get("heart_rate") or s.get("heart_rate_bpm") or 0
    return min(1.0, 0.6*rage + 0.4*max(0, hr-75)/40)

class Proxy:
    def __init__(self):
        self.key   = os.getenv("OPENAI_API_KEY")
        self.use_ai = bool(self.key)
        self.buffers: dict[WebSocket, list[str]] = {}

    async def websocket_proxy(self, client: WebSocket):
        await client.accept();   self.buffers[client] = []
        log.info("Client connected | mode=%s", "OpenAI" if self.use_ai else "local")

        try:
            ai_ws = None
            if self.use_ai:
                ai_ws = await websockets.connect(
                    "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01",
                    extra_headers={"Authorization": f"Bearer {self.key}",
                                   "OpenAI-Beta":"realtime=v1"})
                await ai_ws.send(json.dumps({"type":"session.update",
                                             "session":{"modalities":["text","audio"],
                                                        "voice":"alloy"}}))
            upstream   = asyncio.create_task(self._from_client(client, ai_ws))
            downstream = asyncio.create_task(self._from_openai(ai_ws, client)) if ai_ws else None
            await asyncio.wait({upstream, *( [downstream] if downstream else [])},
                               return_when=asyncio.FIRST_COMPLETED)
        finally:
            self.buffers.pop(client, None)
            if ai_ws: await ai_ws.close()

    # ---------- client → proxy ----------
    async def _from_client(self, client, ai_ws):
        async for raw in client.iter_text():
            m = json.loads(raw); typ = m.get("type")

            if typ == "audio":
                b64 = m.get("audio"); self.buffers[client].append(b64)
                if ai_ws:
                    await ai_ws.send(json.dumps({"type":"input_audio_buffer.append","audio":b64}))

            elif typ == "audio_commit":
                if ai_ws:
                    await ai_ws.send(json.dumps({"type":"input_audio_buffer.commit"}))
                    await ai_ws.send(json.dumps({"type":"response.create",
                                                 "response":{"modalities":["audio","text"]}}))
                else:
                    merged = "".join(self.buffers[client]); self.buffers[client].clear()
                    text   = stt_b64_to_text(merged)
                    await client.send_json({"type":"text_response","text":text})
                    await client.send_json({"type":"text_response_done"})

            elif typ == "text":
                txt = m.get("text","")
                if ai_ws:
                    await ai_ws.send(json.dumps({"type":"conversation.item.create",
                                                 "item":{"type":"message","role":"user",
                                                         "content":[{"type":"input_text","text":txt}]}}))
                    await ai_ws.send(json.dumps({"type":"response.create",
                                                 "response":{"modalities":["audio","text"]}}))
                else:
                    b64 = await tts_mp3_b64(txt)          # ★ Edge-TTS
                    await client.send_json({"type":"audio_response","audio":b64})
                    await client.send_json({"type":"audio_response_done"})

            elif typ == "sensor" and ai_ws:
                prompt = f"Stress {compute_stress(m):.2f}"
                await ai_ws.send(json.dumps({"type":"conversation.item.create",
                                             "item":{"type":"message","role":"user",
                                                     "content":[{"type":"input_text","text":prompt}]}}))
                await ai_ws.send(json.dumps({"type":"response.create",
                                             "response":{"modalities":["audio"]}}))

    # ---------- OpenAI → client ----------
    async def _from_openai(self, ai_ws, client):
        async for raw in ai_ws:
            e = json.loads(raw); et = e.get("type")
            if et == "response.audio.delta":
                b64 = e.get("delta",{}).get("audio")
                if b64: await client.send_json({"type":"audio_response","audio":b64})
            elif et == "response.audio.done":
                await client.send_json({"type":"audio_response_done"})
            elif et == "response.text.delta":
                await client.send_json({"type":"text_response","text":e.get("delta")})
            elif et == "response.text.done":
                await client.send_json({"type":"text_response_done"})
            elif et == "error":
                await client.send_json({"type":"error","error":e.get("error",{})})

proxy = Proxy()

@app.websocket("/v1/realtime")
async def realtime(ws: WebSocket): await proxy.websocket_proxy(ws)

@app.get("/health")
async def health(): return {"mode":"OpenAI" if proxy.use_ai else "local", "status":"ok"}

# ─────────────── start server ────────────────
if __name__ == "__main__":
    log.info("Mode: %s", "OpenAI" if proxy.use_ai else "Edge-TTS / Google-STT local")
    uvicorn.run(app, host="0.0.0.0", port=8081, reload=True)
