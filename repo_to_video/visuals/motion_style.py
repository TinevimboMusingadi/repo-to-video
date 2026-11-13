"""Motion graphics visual engine for modern kinetic tech explainer animations."""

from pathlib import Path
import subprocess
import math
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from ..director.storyboard import Scene
from ..config import TEMP_DIR, get_resolution_dimensions


class MotionGraphicsEngine:
    """Renders sleek modern motion graphics with animated cards, glowing pulses, and gradients."""

    def __init__(self, temp_dir: Path = TEMP_DIR):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.width, self.height = get_resolution_dimensions("720p")  # 1280x720
        self.fps = 30

    def render_scene(self, scene: Scene, target_duration: float, output_mp4: Path) -> Path:
        """
        Renders a motion graphics video clip matching target_duration seconds.
        Pipes raw frames directly into FFmpeg for maximum rendering speed.
        """
        output_mp4 = Path(output_mp4)
        output_mp4.parent.mkdir(parents=True, exist_ok=True)

        total_frames = int(target_duration * self.fps)
        w, h = self.width, self.height

        # Start FFmpeg subprocess listening on stdin pipe
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

        # Precompute gradient background
        bg_array = self._create_gradient_background(w, h)

        nodes = scene.diagram_nodes if scene.diagram_nodes else ["Client", "Engine", "Database"]
        nodes = nodes[:4]

        # Render frames
        for frame_idx in range(total_frames):
            progress = frame_idx / float(max(1, total_frames - 1))
            img = Image.fromarray(bg_array.copy())
            draw = ImageDraw.Draw(img)

            # 1. Header Title & Badge
            self._draw_header(draw, scene.title, progress, w, h)

            # 2. Animated Modular Cards & Connections
            self._draw_cards(draw, nodes, progress, w, h)

            # 3. Animated lower-third instruction
            self._draw_footer(draw, scene.visual_instructions, progress, w, h)

            # Write raw RGB bytes to FFmpeg stdin
            process.stdin.write(img.tobytes())

        process.stdin.close()
        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed while rendering motion graphics scene {scene.scene_id}")

        return output_mp4

    def _create_gradient_background(self, w: int, h: int) -> np.ndarray:
        """Creates a modern dark gradient with radial vignette."""
        x = np.linspace(-1, 1, w)
        y = np.linspace(-1, 1, h)
        xx, yy = np.meshgrid(x, y)
        dist = np.sqrt(xx ** 2 + yy ** 2)

        # Base color #0B0F19 (11, 15, 25) with deep indigo radial glow #1E1B4B (30, 27, 75)
        r = (30 * (1 - dist * 0.7)).clip(10, 35).astype(np.uint8)
        g = (27 * (1 - dist * 0.7)).clip(12, 32).astype(np.uint8)
        b = (75 * (1 - dist * 0.7)).clip(25, 75).astype(np.uint8)

        return np.stack([r, g, b], axis=-1)

    def _draw_header(self, draw: ImageDraw.Draw, title: str, progress: float, w: int, h: int):
        """Draws top title with entrance animation."""
        # Slide down fade
        alpha = min(1.0, progress * 4.0)
        y_offset = int(50 - (1.0 - alpha) * 20)

        # Category badge
        draw.rounded_rectangle([w // 2 - 80, y_offset, w // 2 + 80, y_offset + 28], radius=14, fill=(30, 58, 138))
        draw.text((w // 2, y_offset + 14), "ONBOARDING TOUR", fill=(147, 197, 253), anchor="mm")

        # Main Title
        draw.text((w // 2, y_offset + 55), title[:42], fill=(248, 250, 252), anchor="mm")

        # Thin glowing separator line
        line_w = int(min(w * 0.7, w * 0.7 * alpha))
        draw.line([(w // 2 - line_w // 2, y_offset + 85), (w // 2 + line_w // 2, y_offset + 85)], fill=(59, 130, 246), width=2)

    def _draw_cards(self, draw: ImageDraw.Draw, nodes: list, progress: float, w: int, h: int):
        """Draws kinetic cards arranged horizontally with connecting energy pulses."""
        n = len(nodes)
        card_w = min(220, (w - 180) // max(1, n))
        card_h = 130
        total_w = n * card_w + (n - 1) * 40
        start_x = (w - total_w) // 2
        center_y = h // 2

        card_centers = []

        colors = [
            ((56, 189, 248), (14, 116, 144)),  # Sky
            ((52, 211, 153), (4, 120, 87)),    # Emerald
            ((244, 114, 182), (190, 24, 93)),  # Rose
            ((251, 191, 36), (180, 83, 9))     # Amber
        ]

        # Draw connecting lines first
        for i in range(n - 1):
            c1_x = start_x + i * (card_w + 40) + card_w
            c2_x = start_x + (i + 1) * (card_w + 40)
            mid_y = center_y

            # Base dashed line
            draw.line([(c1_x, mid_y), (c2_x, mid_y)], fill=(51, 65, 85), width=2)

            # Animated moving energy pulse
            pulse_t = (progress * 3.0 + i * 0.3) % 1.0
            pulse_x = c1_x + int((c2_x - c1_x) * pulse_t)
            draw.ellipse([pulse_x - 5, mid_y - 5, pulse_x + 5, mid_y + 5], fill=(96, 165, 250))

        # Draw cards
        for i, node_name in enumerate(nodes):
            x = start_x + i * (card_w + 40)
            y = center_y - card_h // 2

            # Gentle floating effect
            float_offset = int(math.sin(progress * math.pi * 4 + i) * 6)
            y += float_offset

            accent_color, fill_dark = colors[i % len(colors)]

            # Card background
            draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=12, fill=(15, 23, 42), outline=accent_color, width=2)

            # Step pill
            draw.rounded_rectangle([x + 12, y + 12, x + 65, y + 32], radius=6, fill=fill_dark)
            draw.text((x + 38, y + 22), f"0{i+1}", fill=(241, 245, 249), anchor="mm")

            # Node Title
            draw.text((x + card_w // 2, y + 70), node_name[:18], fill=(255, 255, 255), anchor="mm")

            # Status indicator
            draw.ellipse([x + card_w - 24, y + 16, x + card_w - 14, y + 26], fill=accent_color)

    def _draw_footer(self, draw: ImageDraw.Draw, instructions: str, progress: float, w: int, h: int):
        """Draws subtle lower-third visual prompt."""
        clean_inst = (instructions or "").strip()[:70]
        if clean_inst:
            draw.text((w // 2, h - 50), f"• {clean_inst} •", fill=(148, 163, 184), anchor="mm")
