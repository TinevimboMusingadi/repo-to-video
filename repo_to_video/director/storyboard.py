"""Storyboard data models and Gemini AI Director."""

from typing import List, Optional
from pydantic import BaseModel, Field
import json
import re
from google import genai
from google.genai import types

from ..config import GEMINI_API_KEY, GEMINI_TEXT_MODEL
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ..analyzer.scanner import CodebaseDigest


class Scene(BaseModel):
    """A single visual and narrative scene in the onboarding video."""
    scene_id: int
    title: str
    narration: str = Field(description="Exact spoken voiceover narration script.")
    duration_sec: float = Field(default=18.0, description="Estimated target duration in seconds.")
    visual_style: str = Field(default="3b1b", description="Visual style: 3b1b, motion, or tutorial.")
    visual_instructions: str = Field(description="Visual direction and animation cues.")
    diagram_nodes: List[str] = Field(default_factory=list, description="Core component node labels.")
    diagram_edges: List[str] = Field(default_factory=list, description="Connections, e.g. ['A -> B'].")
    code_snippet: Optional[str] = Field(default=None, description="Short code snippet for display.")
    terminal_command: Optional[str] = Field(default=None, description="Quickstart command for terminal.")


class Storyboard(BaseModel):
    """Complete video onboarding storyboard."""
    repo_name: str
    tagline: str
    summary: str
    target_audience: str = "Software Engineers & Contributors"
    scenes: List[Scene]
    total_duration_estimate: float = 90.0


"""Storyboard data models and Gemini AI Director."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import re
from google import genai
from google.genai import types

from ..config import GEMINI_API_KEY, GEMINI_TEXT_MODEL
from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ..analyzer.scanner import CodebaseDigest
from ..audio.gemini_tts import clean_narration_for_tts


class Scene(BaseModel):
    """A single visual and narrative scene in the onboarding video."""
    scene_id: int
    title: str
    narration: str = Field(description="Exact spoken voiceover narration script.")
    duration_sec: float = Field(default=18.0, description="Estimated target duration in seconds.")
    visual_style: str = Field(default="3b1b", description="Visual style: 3b1b, motion, or tutorial.")
    visual_instructions: str = Field(description="Visual direction and animation cues.")
    diagram_nodes: List[str] = Field(default_factory=list, description="Core component node labels.")
    diagram_edges: List[str] = Field(default_factory=list, description="Connections, e.g. ['A -> B'].")
    code_snippet: Optional[str] = Field(default=None, description="Short code snippet for display.")
    terminal_command: Optional[str] = Field(default=None, description="Quickstart command for terminal.")


class Storyboard(BaseModel):
    """Complete video onboarding storyboard."""
    repo_name: str
    tagline: str
    summary: str
    target_audience: str = "Software Engineers & Contributors"
    scenes: List[Scene]
    total_duration_estimate: float = 90.0


class DirectorPreferences(BaseModel):
    """User preferences collected from the interactive intake interview."""
    target_depth: str = Field(
        default="standard",
        description="Video depth: 'quick' (4 scenes, ~1.5 min), 'standard' (6-7 scenes, ~3.5 min), or 'deep_dive' (8-12 scenes, ~6-8 min)."
    )
    target_audience: str = Field(
        default="Software Engineers & Contributors",
        description="Intended audience (e.g. New Contributors, Senior Architects, Full-Stack Devs)."
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Specific modules, directories, or architectural components to spotlight."
    )
    custom_notes: Optional[str] = Field(
        default="",
        description="Custom creator directions, special requirements, or specific workflows to emphasize."
    )
    scene_count: Optional[int] = Field(
        default=None,
        description="Explicit custom scene count if requested."
    )


class StoryboardDirector:
    """Uses Gemini LLM to analyze the codebase and generate an onboarding storyboard."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_TEXT_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def generate_interview_questions(self, digest: CodebaseDigest) -> Dict[str, Any]:
        """
        Extracts detected modules and intelligent intake questions tailored to this codebase.
        Allows the developer to pick video length, audience, and key subsystems.
        """
        candidate_modules: List[str] = []
        if digest.file_tree:
            for line in digest.file_tree.split("\n"):
                line = line.strip()
                if "/" in line or "\\" in line:
                    parts = [p for p in re.split(r"[/\\]", line) if p]
                    if parts and parts[0] and parts[0] not in candidate_modules and not parts[0].startswith("."):
                        candidate_modules.append(parts[0])

        if not candidate_modules:
            candidate_modules = ["Core Engine", "API / Interface", "Data Flow", "Configuration"]

        return {
            "repo_name": digest.repo_name,
            "detected_languages": list(digest.languages.keys()),
            "total_files": digest.total_files,
            "depth_options": [
                {
                    "id": "quick",
                    "label": "Quick Overview",
                    "duration": "~1.5 mins",
                    "scenes": 4,
                    "description": "Fast pitch, high-level mental model, and quickstart setup."
                },
                {
                    "id": "standard",
                    "label": "Standard Onboarding",
                    "duration": "~3.5 mins",
                    "scenes": 6,
                    "description": "Balanced architectural tour, core modules, dataflow lifecycle, and abstractions."
                },
                {
                    "id": "deep_dive",
                    "label": "Comprehensive Deep-Dive",
                    "duration": "~6 to 8 mins",
                    "scenes": 9,
                    "description": "Exhaustive walkthrough: subsystems, internal data structures, pipeline lifecycle, testing & debugging."
                }
            ],
            "audience_options": [
                "New Contributors & Open-Source Hackers",
                "Senior Systems Architects & Tech Leads",
                "Full-Stack Application Developers",
                "DevOps & Infrastructure Engineers"
            ],
            "candidate_modules": candidate_modules[:8],
            "default_focus": candidate_modules[:4]
        }

    def generate_storyboard(
        self,
        digest: CodebaseDigest,
        default_style: str = "3b1b",
        preferences: Optional[DirectorPreferences] = None
    ) -> Storyboard:
        """Generates a complete storyboard tailored to user preferences and codebase digest."""
        prefs = preferences or DirectorPreferences()

        # Determine target scene count based on depth setting
        scene_count = prefs.scene_count
        if not scene_count:
            if prefs.target_depth == "quick":
                scene_count = 4
            elif prefs.target_depth == "deep_dive":
                scene_count = 9
            else:
                scene_count = 6

        if not self.client:
            return self._generate_fallback_storyboard(digest, default_style, prefs, scene_count)

        focus_str = ", ".join(prefs.focus_areas) if prefs.focus_areas else "Core Architecture and Primary Entrypoints"
        custom_notes_str = prefs.custom_notes.strip() if prefs.custom_notes else "Produce a crisp, high-signal developer walkthrough."

        prompt = USER_PROMPT_TEMPLATE.format(
            digest_markdown=digest.to_markdown_summary(),
            target_depth=prefs.target_depth,
            scene_count_target=scene_count,
            target_audience=prefs.target_audience,
            focus_areas=focus_str,
            custom_notes=custom_notes_str
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=Storyboard,
                    temperature=0.4
                )
            )

            raw_text = response.text.strip()
            # Clean markdown JSON fences if returned
            if raw_text.startswith("```"):
                raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
                raw_text = re.sub(r"\n```$", "", raw_text)

            data = json.loads(raw_text)
            storyboard = Storyboard.model_validate(data)

            # Ensure visual styles are set and narrations are sanitized of any meta instructions
            for s in storyboard.scenes:
                if not s.visual_style:
                    s.visual_style = default_style
                s.narration = clean_narration_for_tts(s.narration)

            storyboard.total_duration_estimate = sum(s.duration_sec for s in storyboard.scenes)
            return storyboard

        except Exception as e:
            # Fallback if parsing or API fails
            print(f"[StoryboardDirector] Warning: Gemini structured call failed ({e}), creating fallback storyboard.")
            return self._generate_fallback_storyboard(digest, default_style, prefs, scene_count)

    def _generate_fallback_storyboard(
        self,
        digest: CodebaseDigest,
        default_style: str,
        preferences: Optional[DirectorPreferences] = None,
        target_scenes: int = 6
    ) -> Storyboard:
        """Constructs a deterministic storyboard matching the requested length and modules."""
        prefs = preferences or DirectorPreferences()
        entry = digest.entry_points[0] if digest.entry_points else "main"
        top_langs = list(digest.languages.keys())[:3]
        langs_str = ", ".join(top_langs) if top_langs else "modern code"

        focus_items = prefs.focus_areas if prefs.focus_areas else ["Core Engine", "Pipeline", "Interfaces"]
        primary_focus = focus_items[0] if focus_items else "Core Engine"
        secondary_focus = focus_items[1] if len(focus_items) > 1 else "Data Models"

        all_candidate_scenes = [
            Scene(
                scene_id=1,
                title="The Hook: Introducing " + digest.repo_name,
                narration=f"Welcome to {digest.repo_name}. Built with {langs_str}, this project provides a modular architecture designed for high developer productivity.",
                duration_sec=16.0,
                visual_style=default_style,
                visual_instructions="Title card zooms into project badge with glowing accents and tech grid.",
                diagram_nodes=[digest.repo_name, "Modular Core", "API"],
                diagram_edges=[f"{digest.repo_name} -> Modular Core", "Modular Core -> API"]
            ),
            Scene(
                scene_id=2,
                title="Architecture & High-Level System Map",
                narration="At a high level, the system is organized cleanly into distinct layers: input orchestration, processing engines, and output compositors.",
                duration_sec=18.0,
                visual_style=default_style,
                visual_instructions="Animated node graph showing the core layers connecting with pulsing arrows.",
                diagram_nodes=["Input Layer", "Core Engine", "Output Adapter"],
                diagram_edges=["Input Layer -> Core Engine", "Core Engine -> Output Adapter"]
            ),
            Scene(
                scene_id=3,
                title=f"Deep Dive: {primary_focus} Subsystem",
                narration=f"Let us inspect {primary_focus}. This module manages the primary transformations and business logic, decoupling state from rendering.",
                duration_sec=20.0,
                visual_style=default_style,
                visual_instructions=f"Focused inspection card isolating {primary_focus} with input and output interfaces.",
                diagram_nodes=[primary_focus, "State Engine", "Handler"],
                diagram_edges=[f"{primary_focus} -> State Engine", "State Engine -> Handler"]
            ),
            Scene(
                scene_id=4,
                title="Core Execution & Request Lifecycle",
                narration=f"When an operation begins, execution flows directly through {entry}, initializing the environment and dispatching work tasks to specialized modules.",
                duration_sec=18.0,
                visual_style=default_style,
                visual_instructions="Tracing packet moving from entry point across the component pipeline.",
                diagram_nodes=[entry, "Task Dispatcher", "Worker", "Result Store"],
                diagram_edges=[f"{entry} -> Task Dispatcher", "Task Dispatcher -> Worker", "Worker -> Result Store"],
                code_snippet=list(digest.key_file_samples.values())[0][:200] if digest.key_file_samples else None
            ),
            Scene(
                scene_id=5,
                title=f"Internal Abstractions & {secondary_focus}",
                narration=f"Next, examine {secondary_focus}. Key data structures flow between services through well-defined contracts and validation boundaries.",
                duration_sec=18.0,
                visual_style=default_style,
                visual_instructions=f"Code editor displaying interface specifications and data schemas for {secondary_focus}.",
                diagram_nodes=[secondary_focus, "Data Schema", "Validator"],
                diagram_edges=[f"{secondary_focus} -> Data Schema", "Data Schema -> Validator"]
            ),
            Scene(
                scene_id=6,
                title="Testing & Local Development Loop",
                narration="To maintain high velocity, the repository includes comprehensive unit and integration test suites that simulate end-to-end flows.",
                duration_sec=16.0,
                visual_style=default_style,
                visual_instructions="Split terminal showing test runner execution with passing green badges.",
                diagram_nodes=["Test Runner", "Mock Services", "Integration Suite"],
                diagram_edges=["Test Runner -> Mock Services", "Mock Services -> Integration Suite"],
                terminal_command="pytest -v --tb=short\n# or: python -m unittest discover tests"
            ),
            Scene(
                scene_id=7,
                title="Configuration & Environment Setup",
                narration="Environment configuration is handled declaratively. Secrets and runtime flags are read on boot with graceful fallbacks.",
                duration_sec=16.0,
                visual_style=default_style,
                visual_instructions="Animated configuration card cycling through environment variables and settings.",
                diagram_nodes=[".env Template", "Config Loader", "Validated Settings"],
                diagram_edges=[".env Template -> Config Loader", "Config Loader -> Validated Settings"]
            ),
            Scene(
                scene_id=8,
                title="Extension Points & Contributing Guide",
                narration="Adding a new feature is straightforward: implement the base interface, register your new handler in the module index, and add test coverage.",
                duration_sec=18.0,
                visual_style=default_style,
                visual_instructions="Tree diagram showing an extensible plugin slot being populated by custom logic.",
                diagram_nodes=["Base Interface", "Custom Implementation", "Registry"],
                diagram_edges=["Custom Implementation -> Base Interface", "Custom Implementation -> Registry"]
            ),
            Scene(
                scene_id=9,
                title="Quickstart & Next Steps",
                narration="You are now ready to build. Clone the repository, check out a new feature branch, and submit your first pull request.",
                duration_sec=16.0,
                visual_style=default_style,
                visual_instructions="Terminal window typing the clone and run commands with green success output.",
                terminal_command=f"git clone <repo_url>\ncd {digest.repo_name}\n# Run tests and hack!"
            )
        ]

        # Select scenes matching requested count
        selected_scenes = all_candidate_scenes[:target_scenes]
        # Re-index scene_ids
        for i, s in enumerate(selected_scenes):
            s.scene_id = i + 1
            s.narration = clean_narration_for_tts(s.narration)

        return Storyboard(
            repo_name=digest.repo_name,
            tagline=f"Developer Onboarding Guide for {digest.repo_name}",
            summary=digest.readme_excerpt[:200] or f"Onboarding guide for {digest.repo_name}.",
            target_audience=prefs.target_audience,
            scenes=selected_scenes,
            total_duration_estimate=sum(s.duration_sec for s in selected_scenes)
        )
