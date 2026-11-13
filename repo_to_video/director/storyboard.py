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


class StoryboardDirector:
    """Uses Gemini LLM to analyze the codebase and generate an onboarding storyboard."""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_TEXT_MODEL):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def generate_storyboard(self, digest: CodebaseDigest, default_style: str = "3b1b") -> Storyboard:
        """Generates a complete storyboard from a codebase digest."""
        if not self.client:
            return self._generate_fallback_storyboard(digest, default_style)

        prompt = USER_PROMPT_TEMPLATE.format(digest_markdown=digest.to_markdown_summary())

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
            
            # Ensure visual styles are set
            for s in storyboard.scenes:
                if not s.visual_style:
                    s.visual_style = default_style
            storyboard.total_duration_estimate = sum(s.duration_sec for s in storyboard.scenes)
            return storyboard

        except Exception as e:
            # Fallback if parsing or API fails
            print(f"[StoryboardDirector] Warning: Gemini structured call failed ({e}), creating fallback storyboard.")
            return self._generate_fallback_storyboard(digest, default_style)

    def _generate_fallback_storyboard(self, digest: CodebaseDigest, default_style: str) -> Storyboard:
        """Constructs a deterministic storyboard if LLM call is unavailable."""
        entry = digest.entry_points[0] if digest.entry_points else "main"
        top_langs = list(digest.languages.keys())[:3]
        langs_str = ", ".join(top_langs) if top_langs else "modern code"

        scenes = [
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
                title="Architecture & Bird's-Eye View",
                narration=f"At a high level, the system is organized cleanly into distinct layers: input orchestration, processing engines, and output compositors.",
                duration_sec=18.0,
                visual_style=default_style,
                visual_instructions="Animated node graph showing the 3 core layers connecting with pulsing arrows.",
                diagram_nodes=["Input Layer", "Core Engine", "Output Adapter"],
                diagram_edges=["Input Layer -> Core Engine", "Core Engine -> Output Adapter"]
            ),
            Scene(
                scene_id=3,
                title="Core Execution Flow",
                narration=f"When an operation begins, execution flows directly through {entry}, initializing the environment and dispatching work tasks to specialized modules.",
                duration_sec=18.0,
                visual_style=default_style,
                visual_instructions="Tracing packet moving from entry point across the component pipeline.",
                diagram_nodes=[entry, "Task Dispatcher", "Worker", "Result Store"],
                diagram_edges=[f"{entry} -> Task Dispatcher", "Task Dispatcher -> Worker", "Worker -> Result Store"],
                code_snippet=list(digest.key_file_samples.values())[0][:200] if digest.key_file_samples else None
            ),
            Scene(
                scene_id=4,
                title="Quickstart & Contributing",
                narration=f"Getting started is simple. Clone the repository, configure your environment variables, and run the test suite to verify your setup.",
                duration_sec=16.0,
                visual_style=default_style,
                visual_instructions="Terminal window typing the clone and run commands with green success output.",
                terminal_command=f"git clone <repo_url>\ncd {digest.repo_name}\n# Run tests and hack!"
            )
        ]

        return Storyboard(
            repo_name=digest.repo_name,
            tagline=f"Developer Onboarding Guide for {digest.repo_name}",
            summary=digest.readme_excerpt[:200] or f"Onboarding guide for {digest.repo_name}.",
            scenes=scenes,
            total_duration_estimate=sum(s.duration_sec for s in scenes)
        )
