import asyncio
import edge_tts
import os

async def text_to_speech(text: str, output_file: str = "output.mp3") -> None:
    """Synthesize English speech with Microsoft Edge-TTS and save to MP3."""
    communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")  # male? use "en-US-GuyNeural"
    await communicate.save(output_file)
    print(f"Saved to: {output_file}")

def main() -> None:
    text = input("Enter text to synthesize: ").strip()
    output_file = "output.mp3"
    asyncio.run(text_to_speech(text, output_file))

    # Auto-play the file on Windows only
    if os.name == "nt" and os.path.exists(output_file):
        os.system(f'start "" "{output_file}"')

if __name__ == "__main__":   # ← fixed (was "_main_")
    main()
