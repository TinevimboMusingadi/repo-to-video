"""3Blue1Brown / Manim animation visual engine."""

from pathlib import Path
import subprocess
import shutil
import re
from ..director.storyboard import Scene
from ..config import TEMP_DIR


class ManimVisualEngine:
    """Renders mathematical & geometric 3Blue1Brown-style animations using Manim Community."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def render_scene(self, scene: Scene, target_duration: float, output_mp4: Path) -> Path:
        """
        Generates a Manim script for the scene and executes Manim to produce the video clip.
        The animation is timed to match target_duration seconds.
        """
        output_mp4 = Path(output_mp4)
        output_mp4.parent.mkdir(parents=True, exist_ok=True)

        scene_name = f"Scene_{scene.scene_id}"
        script_path = self.temp_dir / f"manim_{scene.scene_id}.py"
        media_dir = self.temp_dir / f"manim_media_{scene.scene_id}"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Generate Python Manim script
        code = self._generate_manim_code(scene, scene_name, target_duration)
        script_path.write_text(code, encoding="utf-8")

        # Run manim (-ql for fast reliable rendering, 854x480 or -qm for 720p)
        cmd = [
            "python", "-m", "manim",
            "-qm",  # 720p 30fps balanced quality and speed
            "--format=mp4",
            str(script_path),
            scene_name,
            "--media_dir", str(media_dir)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"[ManimEngine] Error rendering {scene_name}: {result.stderr.strip()[:300]}")
            # Fallback to -ql if -qm failed
            cmd[1] = "-ql"
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        # Locate rendered MP4
        rendered_mp4s = list(media_dir.rglob(f"{scene_name}.mp4"))
        if rendered_mp4s:
            shutil.copy2(rendered_mp4s[0], output_mp4)
            return output_mp4

        raise RuntimeError(f"Manim failed to produce video for scene {scene.scene_id}")

    def _generate_manim_code(self, scene: Scene, scene_class_name: str, duration: float) -> str:
        """Generates the Manim Python scene code matching 3b1b aesthetic."""
        safe_title = self._escape_text(scene.title)
        
        # Determine nodes to display
        nodes = scene.diagram_nodes if scene.diagram_nodes else ["Input", "Core Engine", "Output"]
        nodes = nodes[:5]  # limit to 5 nodes for clean visual balance

        # Estimate animation times
        anim_time = min(4.0, max(2.0, duration * 0.4))
        wait_time = max(1.0, duration - anim_time)

        # Code block representation if available
        code_lines_raw = (scene.code_snippet or "").strip().splitlines()[:6]
        safe_code = "\\n".join(self._escape_text(l) for l in code_lines_raw)

        return f'''from manim import *

class {scene_class_name}(Scene):
    def construct(self):
        # 3Blue1Brown Dark Background & Theme
        self.camera.background_color = "#0B0F19"

        # Title Card
        title = Text("{safe_title}", font_size=34, color="#38BDF8", weight=BOLD)
        title.to_edge(UP, buff=0.6)
        
        # Subtitle / Accent Line
        underline = Line(LEFT * 4, RIGHT * 4, color="#818CF8", stroke_width=2)
        underline.next_to(title, DOWN, buff=0.2)

        self.play(FadeIn(title, shift=DOWN*0.3), Create(underline), run_time=1.2)

        # Geometric Node Network
        nodes_text = {repr([self._escape_text(n) for n in nodes])}
        m_nodes = []
        colors = ["#38BDF8", "#34D399", "#F472B6", "#FBBF24", "#A78BFA"]

        for i, name in enumerate(nodes_text):
            col = colors[i % len(colors)]
            circ = RoundedRectangle(corner_radius=0.2, height=1.0, width=2.2, color=col, fill_opacity=0.2)
            lbl = Text(name[:16], font_size=18, color=WHITE)
            node_grp = VGroup(circ, lbl)
            m_nodes.append(node_grp)

        nodes_group = VGroup(*m_nodes).arrange(RIGHT, buff=0.6)
        nodes_group.move_to(ORIGIN + DOWN * 0.2)

        # Arrows between nodes
        arrows = []
        for i in range(len(m_nodes) - 1):
            arr = Arrow(m_nodes[i].get_right(), m_nodes[i+1].get_left(), buff=0.1, color="#64748B", max_tip_length_to_length_ratio=0.25)
            arrows.append(arr)

        if arrows:
            self.play(
                LaggedStart(*[FadeIn(n, scale=0.8) for n in m_nodes], lag_ratio=0.2),
                *[Create(a) for a in arrows],
                run_time={anim_time:.2f}
            )
            # Pulse the core middle node
            if len(m_nodes) > 1:
                target_node = m_nodes[min(1, len(m_nodes)-1)]
                self.play(Indicate(target_node, color="#F59E0B", scale_factor=1.1), run_time=1.0)
        else:
            self.play(FadeIn(nodes_group), run_time={anim_time:.2f})

        # Wait to sync with narration
        self.wait({wait_time:.2f})
'''

    def _escape_text(self, text: str) -> str:
        """Escapes text for safe inclusion in Manim Text strings."""
        if not text:
            return ""
        # Remove quotes, backslashes, and curly braces that could break python string
        clean = text.replace("\\", "/").replace('"', "'").replace("\n", " ").strip()
        return clean[:36]
