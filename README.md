# 🎬 Repo-to-Video: Codebase Onboarding Agent Harness

> Transform any GitHub repository or local codebase into an engaging, animated developer onboarding video with **Gemini AI**, **Manim (3Blue1Brown)**, **Motion Graphics**, and **Studio Voiceover**.

---

## ✨ Features

- 🔍 **Automated Codebase Ingestion & AST Analysis**:
  - Clones public/private repositories into an isolated workspace.
  - Recursively maps directory tree, language distribution, dependency manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`), and entry points.
  - Extracts key code samples and README documentation into an architectural digest.

- 🧠 **Gemini AI Director**:
  - Automatically structures a multi-scene onboarding narrative (Hook & Mission, Bird's-Eye Architecture, Core Engine Flow, Key Abstractions, and Quickstart).
  - Drafts spoken voiceover scripts, visual animation cues, and node connection graphs.

- 🎨 **3 Visual Animation Styles**:
  1. **3Blue1Brown Style (`3b1b`)**: Geometric nodes, glowing graph transformations, and mathematical vectors powered by **Manim Community**.
  2. **Motion Graphics Style (`motion`)**: Sleek kinetic UI cards, pulsing connection traces, and deep tech gradient canvases.
  3. **Developer Code-Walk Style (`tutorial`)**: Split-screen developer IDE with file tree explorer, line-highlighted code editor, and simulated animated terminal commands.

- 🎙️ **Voiceover & Audio Synthesis**:
  - **Gemini 2.5 TTS**: Generates natural speech narration from the script using `gemini-2.5-flash-preview-tts`.
  - **Procedural Ambient Music**: Synthesizes lush ambient electronic background chord pads dynamically tailored to video duration.
  - **FFmpeg Ducking & Subtitles**: Automatically ducks background music volume during speech and exports `.srt` subtitle files.

- 🖥️ **Human-in-the-Loop Web Dashboard & CLI**:
  - Interactive **Streamlit** dashboard to inspect analysis, edit scene narrations, select visual styles, tune audio, and preview videos in an embedded player.
  - Full-featured **CLI** for headless batch processing.

---

## 🚀 Quickstart

### 1. Installation

Ensure Python 3.10+, Node.js, and FFmpeg are available.

```bash
# Clone this repository
git clone https://github.com/TinevimboMusingadi/repo-to-video.git
cd repo-to-video

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TTS_MODEL=gemini-2.5-flash-preview-tts
GEMINI_TEXT_MODEL=gemini-flash-latest
```

---

## 💻 Usage

### Option A: Interactive Web Dashboard (Recommended)

Launch the web harness:

```bash
python main.py --ui
```
or:
```bash
streamlit run repo_to_video/app.py
```

1. Enter a GitHub URL or local path.
2. Click **Analyze Codebase**.
3. Review and edit the generated storyboard in **Step 2**.
4. Choose your visual style (3Blue1Brown, Motion Graphics, or Tutorial).
5. Click **Render Onboarding Video** and watch your generated MP4 in the player!

---

### Option B: Command Line Interface (CLI)

Run headless generation directly from your terminal:

```bash
# Generate a 3Blue1Brown style onboarding video for a repository
python main.py --repo https://github.com/psf/requests --style 3b1b

# Generate a Motion Graphics onboarding video for the current directory
python main.py --repo . --style motion

# Generate a Developer Code-Walk tutorial video
python main.py --repo . --style tutorial --output my_code_walk.mp4
```

---

## 🧪 Testing

Run the automated test suite:

```bash
# Run all unit and integration tests
python -m unittest discover tests -v
```

Tests include:
- `test_analyzer.py`: Codebase scanning and digest verification.
- `test_audio.py`: Procedural ambient music, TTS fallback, audio sequencing, and SRT subtitles.
- `test_visuals.py`: Motion Graphics, Tutorial split-screen IDE, and Video Assembler.
- `test_pipeline.py`: Full end-to-end integration test with audio-video synchronization.

---

## 📁 Repository Structure

```text
repo-to-video/
├── main.py                     # Root entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── repo_to_video/              # Core package
│   ├── config.py               # Settings and directory configuration
│   ├── pipeline.py             # End-to-end orchestration pipeline
│   ├── cli.py                  # Command-line interface
│   ├── app.py                  # Streamlit Web Dashboard
│   ├── analyzer/               # Repo cloning, scanning & digests
│   │   ├── git_manager.py
│   │   └── scanner.py
│   ├── director/               # AI Storyboard & Gemini prompts
│   │   ├── prompts.py
│   │   └── storyboard.py
│   ├── audio/                  # Gemini TTS, ambient music & mixing
│   │   ├── gemini_tts.py
│   │   ├── music_generator.py
│   │   └── audio_mixer.py
│   ├── visuals/                # 3b1b Manim, Motion Graphics, Tutorial
│   │   ├── manim_style.py
│   │   ├── motion_style.py
│   │   └── tutorial_style.py
│   └── compositor/             # FFmpeg multiplexing & subtitles
│       └── video_assembler.py
├── output/                     # Generated MP4 videos and SRT files
└── tests/                      # Automated test suite
```

---

## 📄 License

Apache-2.0
