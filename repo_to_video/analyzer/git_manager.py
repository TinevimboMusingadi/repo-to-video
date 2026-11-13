"""Git manager to clone, inspect, and isolate repository workspaces."""

from pathlib import Path
import subprocess
import shutil
import re
from ..config import WORKSPACE_DIR


class GitManager:
    """Manages repository cloning and local workspace access."""

    def __init__(self, workspace_root: Path = WORKSPACE_DIR):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def prepare_repo(self, repo_target: str) -> tuple[Path, str]:
        """
        Prepares a repository for analysis.
        Accepts either a Git remote URL or a local folder path.
        Returns (local_repo_path, repo_name).
        """
        repo_target = repo_target.strip()
        local_path = Path(repo_target)

        # Check if it's already a local path
        if local_path.exists() and local_path.is_dir():
            repo_name = local_path.name
            return local_path.resolve(), repo_name

        # Otherwise treat as remote Git repository URL
        repo_name = self._extract_repo_name(repo_target)
        dest_dir = self.workspace_root / repo_name

        if dest_dir.exists() and (dest_dir / ".git").exists():
            # Already cloned, fetch latest
            try:
                subprocess.run(
                    ["git", "pull", "--ff-only"],
                    cwd=dest_dir,
                    capture_output=True,
                    timeout=30,
                    check=False
                )
            except Exception:
                pass
            return dest_dir, repo_name

        # If dest exists but is not clean, remove it
        if dest_dir.exists():
            shutil.rmtree(dest_dir, ignore_errors=True)

        # Clone repository
        clone_cmd = ["git", "clone", "--depth", "1", repo_target, str(dest_dir)]
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to clone repository '{repo_target}': {result.stderr.strip()}")

        return dest_dir, repo_name

    def _extract_repo_name(self, url: str) -> str:
        """Extracts a sanitized folder name from a Git URL."""
        cleaned = url.rstrip("/")
        if cleaned.endswith(".git"):
            cleaned = cleaned[:-4]
        name = cleaned.split("/")[-1]
        # Sanitize name
        name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name)
        return name or "repository"
