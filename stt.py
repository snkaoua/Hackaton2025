#!/usr/bin/env python3
"""
stt_run.py  –  Command-line launcher: convert speech in an audio file to text
-----------------------------------------------------------------------------
dependencies:  pip install SpeechRecognition
               # אם תרצי לעבוד עם מיקרופון גם → pip install pipwin && pipwin install pyaudio
"""

import os
import speech_recognition as sr


def speech_to_text(input_file: str, lang: str = "en-US") -> str:
    """
    Convert speech in an audio file (WAV/AIFF/FLAC) to text using Google Web API.

    Parameters
    ----------
    input_file : str
        Path to the audio file.
    lang : str
        BCP-47 language tag (e.g., "en-US", "en-GB", "en-IN").

    Returns
    -------
    str
        Recognised text, or an error message.
    """
    if not os.path.exists(input_file):
        return "File not found. Please verify the path."

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(input_file) as source:
            audio_data = recognizer.record(source)

        return recognizer.recognize_google(audio_data, language=lang)

    except Exception as e:
        return f"Transcription error: {e}"


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main() -> None:
    print("Speech-to-Text (Google Web API)")
    audio_path = input("Enter path to audio file (WAV/AIFF/FLAC): ").strip('" ')
    lang_tag   = input("Language tag [default en-US]: ").strip() or "en-US"

    print("\nTranscribing…\n")
    text = speech_to_text(audio_path, lang_tag)
    print("———  Transcript  ———")
    print(text)
    print("—————————————")


if __name__ == "__main__":
    main()
