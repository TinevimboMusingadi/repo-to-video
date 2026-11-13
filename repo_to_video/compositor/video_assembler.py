"""Video assembler to stitch scene clips, synchronize audio, and export final MP4."""

from pathlib import Path
import subprocess
import shutil
from typing import List
from ..config import OUTPUT_DIR, TEMP_DIR


class VideoAssembler:
    """Assembles scene video clips with master audio and exports the final onboarding MP4."""

    def __init__(self, output_dir: Path = OUTPUT_DIR, temp_dir: Path = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def assemble(
        self,
        scene_video_clips: List[Path],
        master_audio_path: Path,
        output_filename: str = "onboarding_video.mp4",
        burn_subtitles: bool = False,
        subtitles_path: Path = None
    ) -> Path:
        """
        Combines scene video clips, synchronizes with the master audio track,
        and outputs a web-optimized MP4 (H.264 + AAC).
        """
        final_output = self.output_dir / output_filename
        final_output.parent.mkdir(parents=True, exist_ok=True)

        if not scene_video_clips:
            raise ValueError("No video clips provided for assembly.")

        # 1. Create FFmpeg concat manifest
        concat_manifest_path = self.temp_dir / "video_concat_list.txt"
        manifest_lines = []
        for clip in scene_video_clips:
            # Use forward slashes for cross-platform ffmpeg path parsing
            clean_path = str(clip.resolve()).replace("\\", "/")
            manifest_lines.append(f"file '{clean_path}'")
        concat_manifest_path.write_text("\n".join(manifest_lines), encoding="utf-8")

        # 2. Intermediate silent video concatenation
        concatenated_video = self.temp_dir / "concatenated_visuals.mp4"
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_manifest_path),
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(concatenated_video)
        ]
        res_concat = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=180)
        if res_concat.returncode != 0:
            raise RuntimeError(f"FFmpeg video concatenation failed: {res_concat.stderr.strip()[:300]}")

        # 3. Multiplex video with master audio
        mux_cmd = [
            "ffmpeg", "-y",
            "-i", str(concatenated_video),
            "-i", str(master_audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(final_output)
        ]

        res_mux = subprocess.run(mux_cmd, capture_output=True, text=True, timeout=180)
        if res_mux.returncode != 0:
            raise RuntimeError(f"FFmpeg audio-video multiplexing failed: {res_mux.stderr.strip()[:300]}")

        return final_output
