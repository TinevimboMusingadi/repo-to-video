"""Command-Line Interface (CLI) for Repo-to-Video Onboarding Agent Harness."""

import argparse
import sys
import subprocess
from pathlib import Path

from .pipeline import RepoToVideoPipeline
from .config import DEFAULT_STYLE, OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(
        prog="repo-to-video",
        description="Transform any Git repository into an engaging onboarding explainer video."
    )

    parser.add_argument(
        "-r", "--repo",
        type=str,
        default=".",
        help="GitHub URL or local folder path of the repository."
    )
    parser.add_argument(
        "-s", "--style",
        type=str,
        choices=["3b1b", "motion", "tutorial"],
        default=DEFAULT_STYLE,
        help="Visual animation style: 3b1b (Manim), motion (Kinetic cards), tutorial (IDE & Terminal)."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Custom output filename for the MP4 video."
    )
    parser.add_argument(
        "--ui", "--serve",
        action="store_true",
        help="Launch the modern React Web Dashboard and API server."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for the React Web Dashboard (default: 8080)."
    )

    args = parser.parse_args()

    if args.ui:
        import uvicorn
        print("=" * 65)
        print("🎬 REPO-TO-VIDEO REACT WEB DASHBOARD")
        print("=" * 65)
        print(f"🚀 Server running at: http://localhost:{args.port}")
        print("=" * 65)
        uvicorn.run("repo_to_video.server:app", host="0.0.0.0", port=args.port, reload=False)
        return

    print("=" * 65)
    print("🎬 REPO-TO-VIDEO ONBOARDING AGENT HARNESS")
    print("=" * 65)
    print(f"Target Repository : {args.repo}")
    print(f"Visual Style      : {args.style}")
    print("-" * 65)

    pipeline = RepoToVideoPipeline()

    def progress_callback(msg: str, val: float):
        pct = int(val * 100)
        bar = ("#" * (pct // 4)).ljust(25)
        print(f"[{bar}] {pct:3d}% : {msg}")

    try:
        # Step 1: Analyze
        repo_path, repo_name, digest = pipeline.analyze_repository(args.repo, progress_cb=progress_callback)
        print(f"✔ Codebase analyzed: {repo_name} ({digest.total_files} files, {len(digest.languages)} languages)")

        # Step 2: Storyboard
        storyboard = pipeline.draft_storyboard(digest, style=args.style, progress_cb=progress_callback)
        print(f"✔ Storyboard drafted: {len(storyboard.scenes)} scenes planned.")

        # Step 3: Render
        result = pipeline.render_video(storyboard, style=args.style, progress_cb=progress_callback)
        
        print("=" * 65)
        print(f"🎉 SUCCESS! Onboarding video generated:")
        print(f"📹 Video: {result['video_path']}")
        print(f"📄 Subtitles: {result['subtitles_path']}")
        print(f"⏱️ Duration: {result['total_duration']:.1f} seconds")
        print("=" * 65)

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
