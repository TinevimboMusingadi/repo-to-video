"""Gemini TTS engine for natural codebase explainer narration."""

from pathlib import Path
import wave
import math
import struct
import re
from google import genai
from google.genai import types

from ..config import GEMINI_API_KEY, TTS_MODEL, TEMP_DIR


def clean_narration_for_tts(text: str) -> str:
    """
    Cleans raw storyboard narration text so TTS synthesizes pure, natural speech
    without pronouncing prompt meta-instructions, stage directions, or markdown symbols.
    """
    if not text:
        return ""

    cleaned = text
    # Remove bracketed stage directions e.g. [pause], [upbeat music], [Visual cue: ...]
    cleaned = re.sub(r"\[(?:visual|animation|audio|music|sound|pause|stage|note|cue|cut|scene|screen)[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    
    # Parenthesized directions e.g. (read carefully...), (pause), (visual...)
    cleaned = re.sub(r"\((?:read\s+carefully|note|pause|visual|animation|camera|voiceover|cue)[^\)]*\)", "", cleaned, flags=re.IGNORECASE)

    # Remove common narration meta prefixes at line starts
    cleaned = re.sub(r"^(?:narration|narrator|voiceover|speaker|script|developer|read carefully[^:]*):\s*", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

    # Strip markdown formatting: bold, italic, headers, backticks, blockquotes
    cleaned = re.sub(r"[*_~`#>]", "", cleaned)

    # Strip code block fences if mistakenly embedded in speech
    cleaned = re.sub(r"```[\s\S]*?```", "", cleaned)

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class GeminiTTS:
    """Synthesizes high-fidelity narration audio using Gemini TTS."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = TTS_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def synthesize_scene(self, text: str, output_path: Path, scene_id: int = 1) -> float:
        """
        Synthesizes speech for a single scene script.
        Returns the duration of the generated audio in seconds.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sanitize narration text to prevent pronouncing meta instructions or markdown
        speech_text = clean_narration_for_tts(text)
        if not speech_text:
            speech_text = text.strip() or "Onboarding scene overview."

        if not self.client:
            return self._generate_fallback_audio(speech_text, output_path)

        try:
            # Request audio modality from Gemini TTS with pure spoken text only
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=speech_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    system_instruction="You are an engaging professional tech documentary narrator. Read only the exact provided speech text directly, clearly and naturally, without repeating instructions or adding introductory remarks."
                )
            )

            audio_bytes = None
            sample_rate = 24000

            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        audio_bytes = part.inline_data.data
                        # Extract sample rate if present in mime_type
                        if "rate=" in (part.inline_data.mime_type or ""):
                            try:
                                rate_str = part.inline_data.mime_type.split("rate=")[-1].split(";")[0]
                                sample_rate = int(rate_str)
                            except Exception:
                                sample_rate = 24000
                        break

            if not audio_bytes:
                print(f"[GeminiTTS] No audio data in response for scene {scene_id}, using fallback.")
                return self._generate_fallback_audio(text, output_path)

            # Check if Gemini returned a complete WAV file (e.g. from gemini-3.8-flash-tts)
            if audio_bytes.startswith(b"RIFF"):
                output_path.write_bytes(audio_bytes)
                with wave.open(str(output_path), "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = float(frames) / float(rate)
            else:
                # Raw 16-bit linear PCM WAV
                with wave.open(str(output_path), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_bytes)
                duration = len(audio_bytes) / (sample_rate * 2)

            return max(duration, 3.0)

        except Exception as e:
            print(f"[GeminiTTS] Error synthesizing speech for scene {scene_id} ({e}), using fallback.")
            return self._generate_fallback_audio(text, output_path)

    def _generate_fallback_audio(self, text: str, output_path: Path) -> float:
        """Generates a pleasant rhythmic notification tone sequence matching estimated word duration."""
        # Estimate duration based on speaking speed ~140 words per minute (~2.3 words/sec)
        words = len(text.split())
        duration = max(float(words) / 2.3, 4.0)

        sample_rate = 24000
        total_samples = int(sample_rate * duration)
        
        # Soft modulated carrier tone (440Hz and harmonic intervals with decay)
        raw_frames = bytearray()
        for i in range(total_samples):
            t = float(i) / sample_rate
            # Mild rhythmic soft pulses representing words
            pulse = math.sin(2 * math.pi * 3.0 * t) ** 2
            val = int(2000 * pulse * math.sin(2 * math.pi * 320 * t) * math.exp(-0.2 * (t % 1.5)))
            # Clamp to 16-bit
            val = max(-32768, min(32767, val))
            raw_frames.extend(struct.pack("<h", val))

        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(raw_frames)

        return duration
