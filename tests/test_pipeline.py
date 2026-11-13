"""End-to-end integration test for the Repo-to-Video pipeline."""

import unittest
from pathlib import Path

from repo_to_video.pipeline import RepoToVideoPipeline
from repo_to_video.director.storyboard import Storyboard, Scene
from repo_to_video.config import PROJECT_ROOT, TEMP_DIR, OUTPUT_DIR


class TestEndToEndPipeline(unittest.TestCase):
    def test_pipeline_execution(self):
        pipeline = RepoToVideoPipeline(output_dir=OUTPUT_DIR, temp_dir=TEMP_DIR)

        # 1. Analyze this repository
        repo_path, repo_name, digest = pipeline.analyze_repository(str(PROJECT_ROOT))
        self.assertEqual(repo_name, PROJECT_ROOT.name)
        self.assertGreater(digest.total_files, 0)

        # 2. Build a compact 2-scene storyboard for rapid testing
        test_storyboard = Storyboard(
            repo_name="repo_to_video_test",
            tagline="Codebase Onboarding Explainer",
            summary="A quick walkthrough of the repository.",
            scenes=[
                Scene(
                    scene_id=1,
                    title="Introduction to Repo-to-Video",
                    narration="Welcome to Repo to Video, turning code into interactive onboarding videos.",
                    duration_sec=3.0,
                    visual_style="motion",
                    visual_instructions="Show introductory cards",
                    diagram_nodes=["Scanner", "Director", "Renderer"]
                ),
                Scene(
                    scene_id=2,
                    title="Developer Quickstart",
                    narration="Getting started is simple. Clone the repository and run python main dot py.",
                    duration_sec=3.0,
                    visual_style="tutorial",
                    visual_instructions="Show terminal with command",
                    terminal_command="python main.py --ui"
                )
            ]
        )

        # 3. Render video
        result = pipeline.render_video(test_storyboard, style="motion")
        video_path = Path(result["video_path"])
        subtitles_path = Path(result["subtitles_path"])

        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 5000)
        self.assertTrue(subtitles_path.exists())
        self.assertGreater(result["total_duration"], 2.0)


if __name__ == "__main__":
    unittest.main()
