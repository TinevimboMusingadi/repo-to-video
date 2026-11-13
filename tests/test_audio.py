"""Tests for audio synthesis, procedural music generation, and mixing."""

import unittest
from pathlib import Path
import wave

from repo_to_video.audio.gemini_tts import GeminiTTS
from repo_to_video.audio.music_generator import ProceduralMusicGenerator
from repo_to_video.audio.audio_mixer import AudioMixer
from repo_to_video.config import TEMP_DIR


class TestAudioPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = TEMP_DIR / "unit_test_audio"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def test_procedural_music_generator(self):
        gen = ProceduralMusicGenerator()
        out_music = self.test_dir / "test_ambient.wav"
        res_path = gen.generate_ambient_track(duration_sec=3.0, output_path=out_music)

        self.assertTrue(res_path.exists())
        with wave.open(str(res_path), "rb") as wf:
            dur = float(wf.getnframes()) / wf.getframerate()
            self.assertGreaterEqual(dur, 2.9)

    def test_fallback_tts_and_sequencing(self):
        tts = GeminiTTS()
        out_speech = self.test_dir / "test_speech.wav"
        # Test synthetic fallback audio generation
        dur = tts._generate_fallback_audio("Testing fallback audio generation for explainer video.", out_speech)
        self.assertTrue(out_speech.exists())
        self.assertGreater(dur, 2.0)

        # Test audio sequencing
        mixer = AudioMixer(temp_dir=self.test_dir)
        combined, timeline, total_dur = mixer.sequence_speech_tracks([
            (1, out_speech, "Testing scene 1 narration.")
        ])
        self.assertTrue(combined.exists())
        self.assertEqual(len(timeline), 1)

        # Test SRT generation
        out_srt = self.test_dir / "test_subs.srt"
        mixer.generate_srt_subtitles(timeline, out_srt)
        self.assertTrue(out_srt.exists())
        content = out_srt.read_text(encoding="utf-8")
        self.assertIn("-->", content)
        self.assertIn("Testing scene 1 narration.", content)


if __name__ == "__main__":
    unittest.main()
