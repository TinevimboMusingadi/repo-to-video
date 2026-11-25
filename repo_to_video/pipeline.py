"""End-to-end Pipeline orchestrator for Repo-to-Video generation."""

from pathlib import Path
from typing import Callable, Optional
import time

from .analyzer.git_manager import GitManager
from .analyzer.scanner import CodebaseScanner, CodebaseDigest
from .director.storyboard import Storyboard, StoryboardDirector, DirectorPreferences
from .audio.gemini_tts import GeminiTTS
from .audio.music_generator import ProceduralMusicGenerator
from .audio.audio_mixer import AudioMixer
from .visuals.manim_style import ManimVisualEngine
from .visuals.motion_style import MotionGraphicsEngine
from .visuals.tutorial_style import TutorialVisualEngine
from .compositor.video_assembler import VideoAssembler
from .config import OUTPUT_DIR, TEMP_DIR, DEFAULT_STYLE


class RepoToVideoPipeline:
    """Orchestrates the entire repository-to-video onboarding pipeline."""

    def __init__(self, output_dir: Path = OUTPUT_DIR, temp_dir: Path = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.git_manager = GitManager()
        self.director = StoryboardDirector()
        self.tts = GeminiTTS()
        self.music_gen = ProceduralMusicGenerator()
        self.audio_mixer = AudioMixer(temp_dir=self.temp_dir)
        self.assembler = VideoAssembler(output_dir=self.output_dir, temp_dir=self.temp_dir)

        # Visual Engines
        self.manim_engine = ManimVisualEngine(temp_dir=self.temp_dir)
        self.motion_engine = MotionGraphicsEngine(temp_dir=self.temp_dir)
        self.tutorial_engine = TutorialVisualEngine(temp_dir=self.temp_dir)

    def analyze_repository(
        self,
        repo_target: str,
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> tuple[Path, str, CodebaseDigest]:
        """
        Stage 1: Prepares repository and extracts codebase digest.
        """
        if progress_cb:
            progress_cb("Cloning / resolving repository...", 0.1)

        repo_path, repo_name = self.git_manager.prepare_repo(repo_target)

        if progress_cb:
            progress_cb(f"Scanning codebase structure for {repo_name}...", 0.2)

        scanner = CodebaseScanner(repo_path)
        digest = scanner.scan()

        return repo_path, repo_name, digest

    def get_intake_questions(self, digest: CodebaseDigest) -> dict:
        """Generates interactive questionnaire options tailored to the scanned codebase."""
        return self.director.generate_interview_questions(digest)

    def draft_storyboard(
        self,
        digest: CodebaseDigest,
        style: str = DEFAULT_STYLE,
        preferences: Optional[DirectorPreferences] = None,
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> Storyboard:
        """
        Stage 2: Gemini AI analyzes the digest and crafts a structured storyboard tailored to intake questions.
        """
        if progress_cb:
            progress_cb("Gemini AI is analyzing architecture and drafting tailored storyboard...", 0.35)

        storyboard = self.director.generate_storyboard(digest, default_style=style, preferences=preferences)
        return storyboard

    def render_video(
        self,
        storyboard: Storyboard,
        style: str = DEFAULT_STYLE,
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> dict:
        """
        Stage 3: Synthesizes audio, renders visual scenes, and composites final MP4.
        """
        total_scenes = len(storyboard.scenes)
        scene_audio_files = []

        # 1. Audio Synthesis for all scenes
        if progress_cb:
            progress_cb("Synthesizing narration audio via Gemini TTS...", 0.45)

        scene_durations = {}
        for i, scene in enumerate(storyboard.scenes):
            audio_out = self.temp_dir / f"speech_scene_{scene.scene_id}.wav"
            dur = self.tts.synthesize_scene(scene.narration, audio_out, scene_id=scene.scene_id)
            scene_durations[scene.scene_id] = dur
            scene_audio_files.append((scene.scene_id, audio_out, scene.narration))

        # 2. Sequence speech & create timeline
        combined_speech, timeline, total_speech_dur = self.audio_mixer.sequence_speech_tracks(scene_audio_files)

        # 3. Generate background music
        if progress_cb:
            progress_cb("Synthesizing procedural ambient music track...", 0.55)

        music_out = self.temp_dir / "ambient_background.wav"
        self.music_gen.generate_ambient_track(total_speech_dur + 2.0, music_out)

        # 4. Mix speech and background music
        master_audio = self.temp_dir / "master_soundtrack.wav"
        self.audio_mixer.mix_speech_and_music(combined_speech, music_out, master_audio)

        # 5. Export SRT subtitles
        subtitles_out = self.output_dir / f"{storyboard.repo_name}_subtitles.srt"
        self.audio_mixer.generate_srt_subtitles(timeline, subtitles_out)

        # 6. Render Visual Scenes
        scene_clips = []
        for idx, scene in enumerate(storyboard.scenes):
            step_progress = 0.60 + (0.30 * (idx / total_scenes))
            if progress_cb:
                progress_cb(f"Rendering visual scene {idx+1}/{total_scenes} [{style}]: {scene.title[:30]}...", step_progress)

            clip_out = self.temp_dir / f"clip_scene_{scene.scene_id}.mp4"
            target_dur = scene_durations.get(scene.scene_id, scene.duration_sec) + 0.4

            # Route to selected engine
            scene_style = scene.visual_style or style
            if scene_style == "3b1b":
                self.manim_engine.render_scene(scene, target_dur, clip_out)
            elif scene_style == "motion":
                self.motion_engine.render_scene(scene, target_dur, clip_out)
            elif scene_style == "tutorial":
                self.tutorial_engine.render_scene(scene, target_dur, clip_out)
            else:
                self.motion_engine.render_scene(scene, target_dur, clip_out)

            scene_clips.append(clip_out)

        # 7. Final Multiplexing & Assembly
        if progress_cb:
            progress_cb("Compositing final video and master audio with FFmpeg...", 0.95)

        final_filename = f"{storyboard.repo_name}_onboarding.mp4"
        final_video_path = self.assembler.assemble(
            scene_video_clips=scene_clips,
            master_audio_path=master_audio,
            output_filename=final_filename,
            subtitles_path=subtitles_out
        )

        if progress_cb:
            progress_cb("Onboarding video ready!", 1.0)

        return {
            "video_path": final_video_path,
            "subtitles_path": subtitles_out,
            "total_duration": total_speech_dur,
            "storyboard": storyboard
        }
