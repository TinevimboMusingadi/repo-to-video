"""Tests for visual engines (Motion Graphics, Tutorial, Manim) and video assembly."""

import unittest
from pathlib import Path

from repo_to_video.director.storyboard import Scene
from repo_to_video.visuals.motion_style import MotionGraphicsEngine
from repo_to_video.visuals.tutorial_style import TutorialVisualEngine
from repo_to_video.visuals.manim_style import ManimVisualEngine
from repo_to_video.compositor.video_assembler import VideoAssembler
from repo_to_video.config import TEMP_DIR, OUTPUT_DIR


class TestVisualEngines(unittest.TestCase):
    def setUp(self):
        self.test_dir = TEMP_DIR / "unit_test_visuals"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.sample_scene = Scene(
            scene_id=1,
            title="System Architecture",
            narration="Here is how the core modules communicate in this repo.",
            duration_sec=2.0,
            visual_style="motion",
            visual_instructions="Show cards with pulses",
            diagram_nodes=["Client", "Engine", "Database"],
            code_snippet="def run():\n    return 'OK'"
        )

    def test_motion_graphics_render(self):
        engine = MotionGraphicsEngine(temp_dir=self.test_dir)
        out_mp4 = self.test_dir / "test_motion.mp4"
        res = engine.render_scene(self.sample_scene, target_duration=1.5, output_mp4=out_mp4)
        self.assertTrue(res.exists())
        self.assertGreater(res.stat().st_size, 1000)

    def test_tutorial_style_render(self):
        engine = TutorialVisualEngine(temp_dir=self.test_dir)
        out_mp4 = self.test_dir / "test_tutorial.mp4"
        res = engine.render_scene(self.sample_scene, target_duration=1.5, output_mp4=out_mp4)
        self.assertTrue(res.exists())
        self.assertGreater(res.stat().st_size, 1000)

    def test_video_assembler(self):
        # Use generated clips and a generated audio file
        motion_engine = MotionGraphicsEngine(temp_dir=self.test_dir)
        clip1 = self.test_dir / "clip1.mp4"
        clip2 = self.test_dir / "clip2.mp4"
        motion_engine.render_scene(self.sample_scene, target_duration=1.0, output_mp4=clip1)
        motion_engine.render_scene(self.sample_scene, target_duration=1.0, output_mp4=clip2)

        # Create dummy audio
        audio_file = TEMP_DIR / "test_mixed.wav"

        assembler = VideoAssembler(output_dir=self.test_dir, temp_dir=self.test_dir)
        final_mp4 = assembler.assemble(
            scene_video_clips=[clip1, clip2],
            master_audio_path=audio_file,
            output_filename="test_final_assembly.mp4"
        )
        self.assertTrue(final_mp4.exists())
        self.assertGreater(final_mp4.stat().st_size, 2000)


if __name__ == "__main__":
    unittest.main()
