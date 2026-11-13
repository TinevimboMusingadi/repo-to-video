"""Configuration and environment management for Repo-to-Video."""

from pathlib import Path
import os
from dotenv import load_dotenv

# Base project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(PROJECT_ROOT / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini Models
GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-flash-latest")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-2.5-flash-preview-tts")

# Video Settings
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "1080p")  # 1080p (1920x1080) or 720p (1280x720)
DEFAULT_STYLE = os.getenv("DEFAULT_STYLE", "3b1b")

# Resolution Mapping
RESOLUTIONS = {
    "1080p": (1920, 1080),
    "720p": (1280, 720),
    "480p": (854, 480)
}

# Directories
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUT_DIR = PROJECT_ROOT / "output"

for dir_path in [WORKSPACE_DIR, TEMP_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def get_resolution_dimensions(resolution_name: str = VIDEO_RESOLUTION) -> tuple[int, int]:
    """Returns width and height for a resolution preset."""
    return RESOLUTIONS.get(resolution_name, (1920, 1080))


def is_gemini_configured() -> bool:
    """Checks whether a valid Gemini API key is configured."""
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)
