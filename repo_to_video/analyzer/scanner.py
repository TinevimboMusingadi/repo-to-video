"""Codebase scanner to extract architecture, tree, dependencies, and code samples."""

from pathlib import Path
from dataclasses import dataclass, field
import json
import re

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    "dist", "build", ".next", "target", ".gradle", ".idea", ".vscode",
    "temp", "output", "workspace", "coverage", ".pytest_cache", ".ruff_cache"
}

IGNORE_FILES = {
    ".DS_Store", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "uv.lock", "poetry.lock", "Cargo.lock"
}

CODE_EXTENSIONS = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
    ".sh": "Shell Script",
    ".html": "HTML",
    ".css": "CSS"
}

ENTRY_POINT_CANDIDATES = [
    "main.py", "app.py", "server.py", "cli.py", "__main__.py",
    "index.ts", "index.js", "src/main.rs", "main.go", "src/index.ts",
    "src/index.js", "src/App.tsx", "src/app.py", "cmd/main.go"
]

MANIFEST_FILES = [
    "package.json", "pyproject.toml", "setup.py", "requirements.txt",
    "Cargo.toml", "go.mod", "pom.xml", "Dockerfile", "docker-compose.yml"
]


@dataclass
class CodebaseDigest:
    """Structured summary of a scanned codebase."""
    repo_name: str
    repo_path: str
    total_files: int
    languages: dict[str, int] = field(default_factory=dict)
    file_tree: str = ""
    manifests: dict[str, str] = field(default_factory=dict)
    readme_excerpt: str = ""
    entry_points: list[str] = field(default_factory=list)
    key_file_samples: dict[str, str] = field(default_factory=dict)

    def to_markdown_summary(self) -> str:
        """Formats the digest into an LLM-friendly context block."""
        lang_str = ", ".join(f"{k} ({v} files)" for k, v in sorted(self.languages.items(), key=lambda x: -x[1])[:5])
        
        md = [
            f"# Codebase Digest: {self.repo_name}",
            f"- **Total Files Scanned**: {self.total_files}",
            f"- **Primary Languages**: {lang_str or 'Unknown'}",
            f"- **Discovered Entry Points**: {', '.join(self.entry_points) or 'None identified'}",
            "",
            "## Project Directory Tree (Key Structure)",
            "```text",
            self.file_tree,
            "```",
            "",
            "## README / Project Overview",
            self.readme_excerpt or "_No README found._",
            "",
            "## Manifests & Dependencies"
        ]

        for fname, content in self.manifests.items():
            md.append(f"### `{fname}`")
            md.append("```text")
            md.append(content[:1000] + ("\n...[truncated]" if len(content) > 1000 else ""))
            md.append("```")

        if self.key_file_samples:
            md.append("\n## Key Code Samples")
            for fpath, code in self.key_file_samples.items():
                ext = Path(fpath).suffix.lstrip(".") or "text"
                md.append(f"### `{fpath}`")
                md.append(f"```{ext}")
                md.append(code[:1500])
                md.append("```")

        return "\n".join(md)


class CodebaseScanner:
    """Scans and extracts structural metadata from a repository folder."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = Path(repo_dir).resolve()
        if not self.repo_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.repo_dir}")

    def scan(self, max_depth: int = 4, max_files: int = 400) -> CodebaseDigest:
        """Performs a comprehensive scan of the repository."""
        languages: dict[str, int] = {}
        all_relative_files: list[str] = []
        file_tree_lines: list[str] = []
        manifests: dict[str, str] = {}
        readme_excerpt = ""
        entry_points: list[str] = []
        key_file_samples: dict[str, str] = {}

        # 1. Scan tree
        count = 0
        for path in sorted(self.repo_dir.rglob("*")):
            if count >= max_files:
                break

            # Filter out ignored dirs
            rel_parts = path.relative_to(self.repo_dir).parts
            if any(part in IGNORE_DIRS or part.startswith(".") for part in rel_parts):
                continue

            if len(rel_parts) > max_depth:
                continue

            rel_str = str(path.relative_to(self.repo_dir)).replace("\\", "/")

            if path.is_file():
                if path.name in IGNORE_FILES:
                    continue

                count += 1
                all_relative_files.append(rel_str)
                ext = path.suffix.lower()
                lang = CODE_EXTENSIONS.get(ext)
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1

                # Check manifests
                if path.name in MANIFEST_FILES and len(manifests) < 4:
                    try:
                        manifests[rel_str] = path.read_text(encoding="utf-8", errors="ignore")[:2000]
                    except Exception:
                        pass

                # Check README
                if path.name.lower() in ("readme.md", "readme.markdown", "readme.txt", "readme"):
                    if not readme_excerpt:
                        try:
                            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                            readme_excerpt = "\n".join(lines[:120])
                        except Exception:
                            pass

                # Check entry points
                for candidate in ENTRY_POINT_CANDIDATES:
                    if rel_str == candidate or rel_str.endswith("/" + candidate):
                        entry_points.append(rel_str)
                        # Sample code
                        try:
                            code_lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                            key_file_samples[rel_str] = "\n".join(code_lines[:70])
                        except Exception:
                            pass

        # Build clean visual tree string
        file_tree_lines = self._build_tree_str(self.repo_dir, max_depth=max_depth)

        # If no entry point sampled yet, sample up to 2 primary code files
        if not key_file_samples:
            for rel_str in all_relative_files:
                ext = Path(rel_str).suffix.lower()
                if ext in (".py", ".ts", ".js", ".rs", ".go") and len(key_file_samples) < 2:
                    p = self.repo_dir / rel_str
                    try:
                        code_lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                        key_file_samples[rel_str] = "\n".join(code_lines[:60])
                    except Exception:
                        pass

        return CodebaseDigest(
            repo_name=self.repo_dir.name,
            repo_path=str(self.repo_dir),
            total_files=len(all_relative_files),
            languages=languages,
            file_tree="\n".join(file_tree_lines[:60]),
            manifests=manifests,
            readme_excerpt=readme_excerpt,
            entry_points=list(set(entry_points))[:6],
            key_file_samples=key_file_samples
        )

    def _build_tree_str(self, root: Path, max_depth: int = 3, prefix: str = "") -> list[str]:
        """Generates a text ASCII tree."""
        lines = []
        try:
            entries = sorted(
                [e for e in root.iterdir() if e.name not in IGNORE_DIRS and not e.name.startswith(".")],
                key=lambda x: (not x.is_dir(), x.name.lower())
            )
        except Exception:
            return lines

        for i, entry in enumerate(entries[:25]):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")

            if entry.is_dir() and max_depth > 1:
                extension = "    " if is_last else "│   "
                sub_lines = self._build_tree_str(entry, max_depth - 1, prefix + extension)
                lines.extend(sub_lines)
        return lines
