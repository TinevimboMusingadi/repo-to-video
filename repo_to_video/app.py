"""Interactive Streamlit Web Dashboard for Repo-to-Video Onboarding Agent Harness."""

import streamlit as st
from pathlib import Path
import os
import json

from repo_to_video.pipeline import RepoToVideoPipeline
from repo_to_video.config import GEMINI_API_KEY, is_gemini_configured, OUTPUT_DIR
from repo_to_video.director.storyboard import Storyboard, Scene

# Set page config
st.set_page_config(
    page_title="Repo-to-Video | Codebase Onboarding Agent Harness",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #818CF8, #C084FC);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .stCard {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-primary { background: #1E3A8A; color: #93C5FD; }
    .badge-success { background: #064E3B; color: #6EE7B7; }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = RepoToVideoPipeline()
    if "digest" not in st.session_state:
        st.session_state.digest = None
    if "storyboard" not in st.session_state:
        st.session_state.storyboard = None
    if "rendered_result" not in st.session_state:
        st.session_state.rendered_result = None
    if "repo_target" not in st.session_state:
        st.session_state.repo_target = "."


init_session_state()

# Header
st.markdown('<div class="main-title">🎬 Repo-to-Video Agent Harness</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Turn any Git repository into an engaging, animated onboarding video with Gemini AI, Manim, and Studio Voiceover.</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key status
    if is_gemini_configured():
        st.success("✔ Gemini API Key Configured")
    else:
        st.error("✖ Gemini API Key Missing")
        api_key_input = st.text_input("Enter Gemini API Key", type="password")
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input
            st.session_state.pipeline = RepoToVideoPipeline()
            st.rerun()

    st.markdown("---")
    st.subheader("Visual Engine Style")
    selected_style = st.selectbox(
        "Default Visual Style",
        options=["3b1b", "motion", "tutorial"],
        format_func=lambda x: {
            "3b1b": "📐 3Blue1Brown (Manim Community)",
            "motion": "✨ Motion Graphics (Kinetic Tech)",
            "tutorial": "💻 Developer Code-Walk (IDE & Terminal)"
        }[x],
        index=0
    )

    st.markdown("---")
    st.subheader("Audio Settings")
    music_vol = st.slider("Ambient Music Volume", min_value=0.05, max_value=0.35, value=0.14, step=0.01)
    st.caption("Music volume is automatically ducked under spoken narration.")

# Main workflow tabs
tab1, tab2, tab3 = st.tabs(["1. 🔍 Repository Ingestion", "2. 📝 Storyboard & Script Review", "3. 🎥 Video Player & Export"])

# TAB 1: Ingestion & Analysis
with tab1:
    st.subheader("Step 1: Ingest & Analyze Codebase")
    col1, col2 = st.columns([3, 1])
    with col1:
        repo_input = st.text_input(
            "GitHub Repository URL or Local Directory Path",
            value=st.session_state.repo_target,
            placeholder="e.g. https://github.com/psf/requests or ."
        )
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("🚀 Analyze Codebase", type="primary", use_container_width=True)

    if analyze_btn and repo_input:
        st.session_state.repo_target = repo_input
        progress_bar = st.progress(0.0)
        status_txt = st.empty()

        def update_progress(msg, val):
            status_txt.info(f"⏳ {msg}")
            progress_bar.progress(val)

        try:
            repo_path, repo_name, digest = st.session_state.pipeline.analyze_repository(
                repo_input,
                progress_cb=update_progress
            )
            st.session_state.digest = digest

            # Draft storyboard
            storyboard = st.session_state.pipeline.draft_storyboard(
                digest,
                style=selected_style,
                progress_cb=update_progress
            )
            st.session_state.storyboard = storyboard

            progress_bar.progress(1.0)
            status_txt.success(f"✔ Analysis complete for **{repo_name}**! Proceed to Tab 2 to review the script.")
        except Exception as e:
            status_txt.error(f"Error during analysis: {e}")

    # Display Digest if available
    if st.session_state.digest:
        d = st.session_state.digest
        st.markdown("---")
        st.markdown(f"### Discovered Codebase: `{d.repo_name}`")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Files Scanned", d.total_files)
        c2.metric("Languages Found", len(d.languages))
        c3.metric("Entry Points", len(d.entry_points))

        col_tree, col_readme = st.columns(2)
        with col_tree:
            st.markdown("#### 📂 Project Structure")
            st.code(d.file_tree or "No tree available", language="text")

        with col_readme:
            st.markdown("#### 📖 README Overview")
            st.text_area("Overview Text", value=d.readme_excerpt[:600] or "No README", height=240, disabled=True)

# TAB 2: Storyboard Review
with tab2:
    st.subheader("Step 2: Human-in-the-Loop Storyboard & Script Review")
    st.write("Review and customize the narration and visuals for each scene before rendering.")

    if not st.session_state.storyboard:
        st.info("Please analyze a repository in Tab 1 to generate a storyboard.")
    else:
        sb: Storyboard = st.session_state.storyboard
        st.markdown(f"**Repository**: `{sb.repo_name}` | **Target Audience**: {sb.target_audience}")

        edited_scenes = []
        for i, scene in enumerate(sb.scenes):
            with st.expander(f"Scene {scene.scene_id}: {scene.title}", expanded=(i == 0)):
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    new_title = st.text_input(f"Scene {i+1} Title", value=scene.title, key=f"title_{i}")
                    new_narration = st.text_area(
                        f"Spoken Narration Script (Voiceover)",
                        value=scene.narration,
                        height=90,
                        key=f"narration_{i}"
                    )
                with col_right:
                    new_style = st.selectbox(
                        f"Visual Style",
                        options=["3b1b", "motion", "tutorial"],
                        index=["3b1b", "motion", "tutorial"].index(scene.visual_style if scene.visual_style in ["3b1b", "motion", "tutorial"] else selected_style),
                        key=f"style_{i}"
                    )
                    new_inst = st.text_input("Visual Animation Cues", value=scene.visual_instructions, key=f"inst_{i}")
                    nodes_str = st.text_input("Diagram Nodes (comma-separated)", value=", ".join(scene.diagram_nodes), key=f"nodes_{i}")

                # Update scene object
                scene.title = new_title
                scene.narration = new_narration
                scene.visual_style = new_style
                scene.visual_instructions = new_inst
                scene.diagram_nodes = [n.strip() for n in nodes_str.split(",") if n.strip()]
                edited_scenes.append(scene)

        sb.scenes = edited_scenes

        st.markdown("---")
        render_col1, render_col2 = st.columns([3, 1])
        with render_col1:
            st.write(f"Estimated Video Length: **~{len(sb.scenes) * 18} seconds** across **{len(sb.scenes)} scenes**.")
        with render_col2:
            render_btn = st.button("🎬 Render Onboarding Video", type="primary", use_container_width=True)

        if render_btn:
            render_progress = st.progress(0.0)
            render_status = st.empty()

            def update_render(msg, val):
                render_status.info(f"⏳ {msg}")
                render_progress.progress(val)

            try:
                res = st.session_state.pipeline.render_video(
                    sb,
                    style=selected_style,
                    progress_cb=update_render
                )
                st.session_state.rendered_result = res
                render_progress.progress(1.0)
                render_status.success("🎉 Video rendered successfully! Switch to Tab 3 to watch.")
            except Exception as e:
                render_status.error(f"Render failed: {e}")

# TAB 3: Video Player & Export
with tab3:
    st.subheader("Step 3: Watch & Export Onboarding Video")

    if not st.session_state.rendered_result:
        # Check if any videos exist in output
        existing_mp4s = list(OUTPUT_DIR.glob("*.mp4"))
        if existing_mp4s:
            st.info("Found previously generated videos in output folder:")
            selected_video = st.selectbox("Select Video", options=existing_mp4s, format_func=lambda p: p.name)
            if selected_video:
                st.video(str(selected_video))
                with open(selected_video, "rb") as vf:
                    st.download_button(
                        label="⬇️ Download Video (MP4)",
                        data=vf,
                        file_name=selected_video.name,
                        mime="video/mp4"
                    )
        else:
            st.info("No video rendered yet. Complete Step 1 and Step 2 to generate your video.")
    else:
        res = st.session_state.rendered_result
        v_path = Path(res["video_path"])
        
        st.success(f"✔ Ready: **{v_path.name}** ({res.get('total_duration', 0):.1f}s)")
        st.video(str(v_path))

        c1, c2 = st.columns(2)
        with c1:
            with open(v_path, "rb") as vf:
                st.download_button(
                    label="⬇️ Download Full Video (.mp4)",
                    data=vf,
                    file_name=v_path.name,
                    mime="video/mp4",
                    use_container_width=True
                )
        with c2:
            sub_path = Path(res.get("subtitles_path", ""))
            if sub_path.exists():
                with open(sub_path, "rb") as sf:
                    st.download_button(
                        label="📄 Download Subtitles (.srt)",
                        data=sf,
                        file_name=sub_path.name,
                        mime="text/plain",
                        use_container_width=True
                    )
