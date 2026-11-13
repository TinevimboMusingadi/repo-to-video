"""Audio mixer to sequence speech, duck background music, and generate subtitles."""

from pathlib import Path
import subprocess
import wave
from typing import List, Tuple
from ..config import TEMP_DIR


class AudioMixer:
    """Sequences scene speech audio, overlays ambient music, and exports subtitles."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def sequence_speech_tracks(
        self,
        scene_audio_files: List[Tuple[int, Path, str]]
    ) -> Tuple[Path, List[dict], float]:
        """
        Concatenates scene audio files with pauses.
        Returns:
            - combined_speech_wav_path
            - scene_timeline (list of {scene_id, start_time, end_time, duration, narration})
            - total_speech_duration
        """
        combined_path = self.temp_dir / "all_speech_combined.wav"
        scene_timeline = []
        current_time = 0.0
        sample_rate = 24000
        pause_duration = 0.4  # seconds pause between scenes
        pause_samples = int(sample_rate * pause_duration)
        pause_bytes = b"\x00\x00" * pause_samples

        all_frames = bytearray()

        for scene_id, wav_path, narration in scene_audio_files:
            wav_path = Path(wav_path)
            if not wav_path.exists():
                continue

            with wave.open(str(wav_path), "rb") as wf:
                sr = wf.getframerate()
                sample_rate = sr
                n_frames = wf.getnframes()
                duration = float(n_frames) / float(sr)
                frames = wf.readframes(n_frames)

            start_time = current_time
            end_time = current_time + duration
            scene_timeline.append({
                "scene_id": scene_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "narration": narration
            })

            all_frames.extend(frames)
            # Add pause between scenes
            all_frames.extend(pause_bytes)
            current_time = end_time + pause_duration

        total_duration = current_time

        with wave.open(str(combined_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(all_frames)

        return combined_path, scene_timeline, total_duration

    def mix_speech_and_music(
        self,
        speech_wav: Path,
        music_wav: Path,
        output_wav: Path,
        music_volume: float = 0.14
    ) -> Path:
        """
        Mixes speech track with background music using FFmpeg.
        Ducks music volume down so narration is crisp and prominent.
        """
        output_wav = Path(output_wav)
        output_wav.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(speech_wav),
            "-i", str(music_wav),
            "-filter_complex",
            f"[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2",
            "-ac", "2",
            "-ar", "44100",
            str(output_wav)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[AudioMixer] FFmpeg mix warning: {result.stderr.strip()[:200]}")
            # Fallback to speech only
            return speech_wav

        return output_wav

    def generate_srt_subtitles(self, scene_timeline: List[dict], output_srt: Path) -> Path:
        """Generates an SRT subtitle file aligned to the scene timeline."""
        output_srt = Path(output_srt)
        output_srt.parent.mkdir(parents=True, exist_ok=True)

        lines = []
        for i, item in enumerate(scene_timeline, start=1):
            start_str = self._format_timestamp(item["start_time"])
            end_str = self._format_timestamp(item["end_time"])
            text = item["narration"].strip()

            lines.append(f"{i}")
            lines.append(f"{start_str} --> {end_str}")
            lines.append(f"{text}\n")

        output_srt.write_text("\n".join(lines), encoding="utf-8")
        return output_srt

    def _format_timestamp(self, seconds: float) -> str:
        """Formats seconds into HH:MM:SS,mmm for SRT."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
