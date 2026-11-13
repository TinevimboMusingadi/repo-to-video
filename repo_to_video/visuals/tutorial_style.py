"""Developer tutorial & code-walk visual engine with IDE, file tree, and terminal."""

from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from ..director.storyboard import Scene
from ..config import TEMP_DIR, get_resolution_dimensions


class TutorialVisualEngine:
    """Renders developer tutorial code-walk videos featuring an IDE editor, file tree, and terminal."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.width, self.height = get_resolution_dimensions("720p")  # 1280x720
        self.fps = 30

    def render_scene(self, scene: Scene, target_duration: float, output_mp4: Path) -> Path:
        """
        Renders an IDE split-screen code-walk video clip matching target_duration.
        """
        output_mp4 = Path(output_mp4)
        output_mp4.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(target_duration * self.fps)
        w, h = self.width, self.height

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{w}x{h}",
            "-pix_fmt", "rgb24",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            str(output_mp4)
        ]

        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

        # Code lines
        code_text = scene.code_snippet or "def main():\n    print('Initializing codebase...')\n    run_engine()\n    return True"
        code_lines = [l.strip("\r") for l in code_text.strip().splitlines()][:10]

        terminal_cmd = scene.terminal_command or "python -m pytest tests/ --verbose"

        # Render frames
        for frame_idx in range(total_frames):
            progress = frame_idx / float(max(1, total_frames - 1))
            img = Image.new("RGB", (w, h), (15, 23, 42))  # Slate 900 background
            draw = ImageDraw.Draw(img)

            # 1. Window Frame & Title Bar
            self._draw_window_frame(draw, scene.title, w, h)

            # 2. Left Sidebar (Project Explorer)
            self._draw_sidebar(draw, scene.diagram_nodes, progress, w, h)

            # 3. Center Code Editor with Animated Highlight
            self._draw_code_editor(draw, code_lines, progress, w, h)

            # 4. Bottom Terminal
            self._draw_terminal(draw, terminal_cmd, progress, w, h)

            process.stdin.write(img.tobytes())

        process.stdin.close()
        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed while rendering tutorial scene {scene.scene_id}")

        return output_mp4

    def _draw_window_frame(self, draw: ImageDraw.Draw, title: str, w: int, h: int):
        """Draws outer desktop window frame with title bar."""
        # Top title bar
        draw.rectangle([0, 0, w, 40], fill=(30, 41, 59))
        draw.line([(0, 40), (w, 40)], fill=(51, 65, 85), width=1)

        # macOS style window buttons
        draw.ellipse([16, 14, 28, 26], fill=(239, 68, 68))    # Red
        draw.ellipse([36, 14, 48, 26], fill=(245, 158, 11))   # Yellow
        draw.ellipse([56, 14, 68, 26], fill=(34, 197, 94))    # Green

        # Title
        draw.text((w // 2, 20), f"Repo Walkthrough - {title[:35]}", fill=(203, 213, 225), anchor="mm")

    def _draw_sidebar(self, draw: ImageDraw.Draw, nodes: list, progress: float, w: int, h: int):
        """Draws file tree navigation sidebar."""
        sidebar_w = 260
        draw.rectangle([0, 41, sidebar_w, h], fill=(15, 23, 42))
        draw.line([(sidebar_w, 41), (sidebar_w, h)], fill=(51, 65, 85), width=1)

        # Explorer header
        draw.text((20, 60), "EXPLORER", fill=(100, 116, 139), anchor="lm")

        items = ["src/", "  models/", "  api/"]
        if nodes:
            for n in nodes[:3]:
                items.append(f"  {n.lower().replace(' ', '_')}.py")
        items.extend(["tests/", "README.md", "pyproject.toml"])

        y = 90
        for i, item in enumerate(items[:10]):
            is_active = (i == 3)
            if is_active:
                draw.rounded_rectangle([4, y - 10, sidebar_w - 4, y + 14], radius=4, fill=(30, 58, 138))
                draw.text((24, y), f"📄 {item}", fill=(96, 165, 250), anchor="lm")
            else:
                prefix = "📁 " if item.endswith("/") else "📄 "
                draw.text((24, y), f"{prefix}{item}", fill=(148, 163, 184), anchor="lm")
            y += 28

    def _draw_code_editor(self, draw: ImageDraw.Draw, code_lines: list, progress: float, w: int, h: int):
        """Draws syntax-highlighted code editor with scanning spotlight highlight."""
        sidebar_w = 260
        terminal_h = 160
        editor_h = h - terminal_h - 41
        editor_x = sidebar_w + 1

        # Editor background
        draw.rectangle([editor_x, 41, w, 41 + editor_h], fill=(2, 6, 23))

        # Editor tab
        draw.rectangle([editor_x, 41, editor_x + 180, 75], fill=(15, 23, 42))
        draw.text((editor_x + 90, 58), "active_module.py", fill=(241, 245, 249), anchor="mm")
        draw.line([(editor_x, 75), (w, 75)], fill=(30, 41, 59), width=1)

        # Code lines
        start_y = 100
        line_height = 26
        active_line_idx = int(progress * len(code_lines)) % max(1, len(code_lines))

        for idx, line in enumerate(code_lines):
            y = start_y + idx * line_height

            # Active line highlight
            if idx == active_line_idx:
                draw.rectangle([editor_x, y - 4, w, y + line_height - 6], fill=(30, 41, 59))
                draw.rectangle([editor_x, y - 4, editor_x + 4, y + line_height - 6], fill=(59, 130, 246))

            # Line number
            draw.text((editor_x + 20, y + 6), f"{idx+1:2d}", fill=(71, 85, 105), anchor="lm")

            # Colored code text
            color = (56, 189, 248) if "def " in line or "class " in line else (226, 232, 240)
            if "import " in line or "from " in line:
                color = (244, 114, 182)
            elif "return" in line:
                color = (251, 191, 36)

            draw.text((editor_x + 55, y + 6), line[:75], fill=color, anchor="lm")

    def _draw_terminal(self, draw: ImageDraw.Draw, terminal_cmd: str, progress: float, w: int, h: int):
        """Draws bottom terminal pane with simulated command typing."""
        sidebar_w = 260
        terminal_h = 160
        term_y = h - terminal_h

        # Terminal pane background
        draw.rectangle([sidebar_w, term_y, w, h], fill=(15, 23, 42))
        draw.line([(sidebar_w, term_y), (w, term_y)], fill=(51, 65, 85), width=1)

        # Tab bar
        draw.text((sidebar_w + 20, term_y + 16), "TERMINAL", fill=(148, 163, 184), anchor="lm")

        # Typing simulation
        typed_len = int(progress * len(terminal_cmd))
        typed_str = terminal_cmd[:typed_len]
        cursor = "█" if int(progress * 10) % 2 == 0 else ""

        draw.text((sidebar_w + 20, term_y + 50), f"$ {typed_str}{cursor}", fill=(52, 211, 153), anchor="lm")

        if progress > 0.6:
            draw.text((sidebar_w + 20, term_y + 85), "✔ Build succeeded. 0 errors, 0 warnings.", fill=(148, 163, 184), anchor="lm")
            draw.text((sidebar_w + 20, term_y + 115), "✔ Tests passed (14/14 suites)", fill=(74, 222, 128), anchor="lm")
