import asyncio, json, os, base64, tempfile
from fastapi import WebSocket
from app.services.stress import compute_stress
from app.tts import text_to_speech
from app.stt import speech_to_text

class AudioProxy:
    def __init__(self):
        self.buffers: dict[WebSocket, list[str]] = {}

    async def websocket_proxy(self, client: WebSocket):
        await client.accept()
        self.buffers[client] = []

        try:
            async for raw in client.iter_text():
                m = json.loads(raw)
                typ = m.get("type")

                if typ == "audio":
                    self.buffers[client].append(m.get("audio"))

                elif typ == "audio_commit":
                    merged = "".join(self.buffers[client])
                    self.buffers[client].clear()
                    text = self._stt_b64_to_text(merged)
                    await client.send_json({"type": "text_response", "text": text})
                    await client.send_json({"type": "text_response_done"})

                elif typ == "text":
                    audio = await self._tts_mp3_b64(m.get("text", ""))
                    await client.send_json({"type": "audio_response", "audio": audio})
                    await client.send_json({"type": "audio_response_done"})

                elif typ == "sensor":
                    prompt = f"Stress {compute_stress(m):.2f}"
                    await client.send_json({"type": "text_response", "text": prompt})
                    await client.send_json({"type": "text_response_done"})

        finally:
            self.buffers.pop(client, None)

    def _stt_b64_to_text(self, b64_wav: str, lang="en-US") -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(base64.b64decode(b64_wav))
            tmp.flush()
            text = speech_to_text(tmp.name, lang=lang)
        os.remove(tmp.name)
        return text

    async def _tts_mp3_b64(self, text: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            out_path = tmp.name
        await text_to_speech(text, out_path)
        mp3_bytes = open(out_path, "rb").read()
        os.remove(out_path)
        return base64.b64encode(mp3_bytes).decode()
