"""
Audio API Examples
Demonstrates various ways to use the R9S audio API (speech, transcription, translation).

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.
"""
from r9s import R9S
import os


def text_to_speech_basic():
    """Example 1: Basic text-to-speech"""
    print("\n" + "="*60)
    print("Example 1: Basic Text-to-Speech")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        response = r9_s.audio.speech(
            model="speech-2.6-turbo",
            input="Hello, welcome to our service!",
            voice="alloy"
        )

        # Save audio to file (response is a streaming response)
        output_file = "output_basic.mp3"
        with open(output_file, "wb") as f:
            f.write(response.read())
        print(f"Audio saved to: {output_file}")


def text_to_speech_with_options():
    """Example 2: Text-to-speech with custom parameters"""
    print("\n" + "="*60)
    print("Example 2: Text-to-Speech with Custom Parameters")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        response = r9_s.audio.speech(
            model="speech-2.6-hd",
            input="The quick brown fox jumps over the lazy dog.",
            voice="nova",
            response_format="mp3",
            speed=1.0
        )

        output_file = "output_detailed.mp3"
        with open(output_file, "wb") as f:
            f.write(response.read())
        print(f"High-quality audio saved to: {output_file}")


def text_to_speech_fast():
    """Example 3: Fast-paced speech for briefings"""
    print("\n" + "="*60)
    print("Example 3: Fast-Paced Speech")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        response = r9_s.audio.speech(
            model="speech-2.6-turbo",
            input="Daily update: traffic is clear, weather is sunny, meetings start at 10 AM.",
            voice="echo",
            response_format="mp3",
            speed=1.2
        )

        output_file = "output_fast.mp3"
        with open(output_file, "wb") as f:
            f.write(response.read())
        print(f"Fast-paced audio saved to: {output_file} (speed: 1.2x)")


def text_to_speech_slow():
    """Example 4: Slow speech for language learning"""
    print("\n" + "="*60)
    print("Example 4: Slow Speech for Language Learning")
    print("="*60)

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        response = r9_s.audio.speech(
            model="speech-2.6-turbo",
            input="Practice makes perfect. Repeat after me slowly.",
            voice="shimmer",
            response_format="mp3",
            speed=0.75
        )

        output_file = "output_slow.mp3"
        with open(output_file, "wb") as f:
            f.write(response.read())
        print(f"Slow-paced audio saved to: {output_file} (speed: 0.75x)")


def transcribe_audio_basic():
    """Example 5: Basic audio transcription"""
    print("\n" + "="*60)
    print("Example 5: Basic Audio Transcription")
    print("="*60)

    # Note: You need to have an audio file to transcribe
    audio_file_path = "output_slow.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.transcribe(
                file={
                    "file_name": "output_slow.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1"
            )

        # Response can be AudioTranscriptionResponse object or str
        if isinstance(response, str):
            print(f"Transcription: {response}")
        else:
            print(f"Transcription: {response.text}")
            if response.language:
                print(f"Detected language: {response.language}")


def transcribe_audio_with_options():
    """Example 6: Audio transcription with parameters"""
    print("\n" + "="*60)
    print("Example 6: Audio Transcription with Parameters")
    print("="*60)

    audio_file_path = "output_slow.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.transcribe(
                file={
                    "file_name": "output_slow.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1",
                language="en",
                response_format="json",
                temperature=0
            )

        # Response can be AudioTranscriptionResponse object or str
        if isinstance(response, str):
            print(f"Transcription: {response}")
        else:
            print(f"Transcription: {response.text}")


def transcribe_audio_with_timestamps():
    """Example 7: Audio transcription with word timestamps"""
    print("\n" + "="*60)
    print("Example 7: Audio Transcription with Word Timestamps")
    print("="*60)

    audio_file_path = "meeting.wav"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.transcribe(
                file={
                    "file_name": "meeting.wav",
                    "content": audio_file.read(),
                },
                model="gpt-4o-transcribe",
                language="en",
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

        # Response can be AudioTranscriptionResponse object or str
        if isinstance(response, str):
            print(f"Transcription: {response}")
        else:
            print(f"Transcription: {response.text}")
            if response.words:
                print(f"\nFirst 5 words with timestamps:")
                for word_info in response.words[:5]:
                    print(f"  {word_info.word} [{word_info.start:.2f}s - {word_info.end:.2f}s]")


def transcribe_audio_srt():
    """Example 8: Generate SRT subtitles"""
    print("\n" + "="*60)
    print("Example 8: Generate SRT Subtitles")
    print("="*60)

    audio_file_path = "video_audio.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.transcribe(
                file={
                    "file_name": "video_audio.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1",
                language="en",
                response_format="srt"
            )

        # Save SRT file (response is str when format is srt)
        srt_file = "subtitles.srt"
        with open(srt_file, "w", encoding="utf-8") as f:
            if isinstance(response, str):
                f.write(response)
            else:
                f.write(response.text)
        print(f"SRT subtitles saved to: {srt_file}")


def transcribe_with_prompt():
    """Example 9: Transcription with technical terms prompt"""
    print("\n" + "="*60)
    print("Example 9: Transcription with Technical Terms Prompt")
    print("="*60)

    audio_file_path = "tech_talk.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.transcribe(
                file={
                    "file_name": "tech_talk.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1",
                language="en",
                prompt="Technical discussion about Kubernetes, Docker, microservices, API gateway",
                response_format="json",
                temperature=0
            )

        # Response can be AudioTranscriptionResponse object or str
        if isinstance(response, str):
            print(f"Transcription: {response}")
        else:
            print(f"Transcription: {response.text}")
        print("Note: The prompt helps improve accuracy for technical terminology")


def translate_audio_basic():
    """Example 10: Basic audio translation to English"""
    print("\n" + "="*60)
    print("Example 10: Basic Audio Translation")
    print("="*60)

    audio_file_path = "german_audio.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.translate(
                file={
                    "file_name": "german_audio.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1"
            )

        # Response can be AudioTranslationResponse object or str
        if isinstance(response, str):
            print(f"English Translation: {response}")
        else:
            print(f"English Translation: {response.text}")
            if response.language:
                print(f"Source language: {response.language}")


def translate_audio_with_prompt():
    """Example 11: Audio translation with contextual prompt"""
    print("\n" + "="*60)
    print("Example 11: Audio Translation with Prompt")
    print("="*60)

    audio_file_path = "french_audio.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.translate(
                file={
                    "file_name": "french_audio.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1",
                prompt="This is about technology",
                response_format="json"
            )

        # Response can be AudioTranslationResponse object or str
        if isinstance(response, str):
            print(f"English Translation: {response}")
        else:
            print(f"English Translation: {response.text}")


def translate_meeting_notes():
    """Example 12: Translate meeting recording to English"""
    print("\n" + "="*60)
    print("Example 12: Translate Meeting Recording")
    print("="*60)

    audio_file_path = "meeting_cn.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.translate(
                file={
                    "file_name": "meeting_cn.mp3",
                    "content": audio_file.read(),
                },
                model="gpt-4o-transcribe",
                prompt="Business meeting, translate clearly",
                response_format="text"
            )

        # Response is str when format is text
        if isinstance(response, str):
            print(f"Meeting Translation:\n{response}")
        else:
            print(f"Meeting Translation:\n{response.text}")


def translate_with_precise_mode():
    """Example 13: Precise translation for legal content"""
    print("\n" + "="*60)
    print("Example 13: Precise Translation (Low Temperature)")
    print("="*60)

    audio_file_path = "legal_audio.mp3"

    if not os.path.exists(audio_file_path):
        print(f"Warning: Audio file '{audio_file_path}' not found. Skipping this example.")
        return

    with R9S(api_key=os.getenv("R9S_API_KEY", "")) as r9_s:
        with open(audio_file_path, "rb") as audio_file:
            response = r9_s.audio.translate(
                file={
                    "file_name": "legal_audio.mp3",
                    "content": audio_file.read(),
                },
                model="whisper-1",
                prompt="Legal document reading, translate accurately",
                response_format="json",
                temperature=0
            )

        # Response can be AudioTranslationResponse object or str
        if isinstance(response, str):
            print(f"Precise Translation: {response}")
        else:
            print(f"Precise Translation: {response.text}")
        print("Note: temperature=0 ensures maximum precision")


def main():
    """Run all examples"""
    examples = [
        ("Basic Text-to-Speech", text_to_speech_basic),
        ("Text-to-Speech with Options", text_to_speech_with_options),
        ("Fast-Paced Speech", text_to_speech_fast),
        ("Slow Speech for Learning", text_to_speech_slow),
        ("Basic Audio Transcription", transcribe_audio_basic),
        ("Transcription with Parameters", transcribe_audio_with_options),
        ("Transcription with Timestamps", transcribe_audio_with_timestamps),
        ("Generate SRT Subtitles", transcribe_audio_srt),
        ("Transcription with Prompt", transcribe_with_prompt),
        ("Basic Audio Translation", translate_audio_basic),
        ("Translation with Prompt", translate_audio_with_prompt),
        ("Translate Meeting Recording", translate_meeting_notes),
        ("Precise Translation", translate_with_precise_mode),
    ]

    print("\n" + "="*60)
    print("R9S Audio API - All Examples")
    print("="*60)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nSelect an example to run (1-13), or 0 to run all:")
    try:
        choice = input("Your choice: ").strip()

        if choice == "0":
            for name, func in examples:
                try:
                    func()
                except Exception as e:
                    print(f"\nError in {name}: {e}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, func = examples[int(choice) - 1]
            func()
        else:
            print("Invalid choice. Running basic text-to-speech example...")
            text_to_speech_basic()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
