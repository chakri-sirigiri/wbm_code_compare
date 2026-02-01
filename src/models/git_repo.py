import subprocess
from pathlib import Path
from typing import Any

from src.utils.logger import setup_logger

from .base import BaseAsset

logger = setup_logger(__name__)


class GitRepo(BaseAsset):
    """Simplified Git repository handler."""

    remote_url: str
    local_path: Path

    def clone_or_pull(self) -> bool:
        """Clone if doesn't exist, otherwise fetch."""
        if not self.local_path.exists():
            logger.info(f"Cloning {self.remote_url} to {self.local_path}...")
            try:
                subprocess.run(
                    ["git", "clone", self.remote_url, str(self.local_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Clone failed: {e.stderr}")
                return False
        else:
            logger.info(f"Repository exists at {self.local_path}, fetching...")
            try:
                subprocess.run(
                    ["git", "fetch", "--all"],
                    cwd=self.local_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Fetch failed: {e.stderr}")
                return False

    def checkout(self, branch_name: str) -> bool:
        """Checkout a specific branch/tag/hash."""
        logger.info(f"Checking out {branch_name} in {self.local_path}...")
        try:
            # Force checkout to discard any local changes in the temp clone
            subprocess.run(
                ["git", "checkout", "-f", branch_name],
                cwd=self.local_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Checkout failed: {e.stderr}")
            return False

    def get_commit_log(self, base_ref: str, head_ref: str) -> list[dict[str, Any]]:
        """Get commits unique to head_ref."""
        try:
            cmd = [
                "git",
                "log",
                f"{base_ref}..{head_ref}",
                "--pretty=format:COMMIT|%h|%an|%ad|%s",
                "--date=iso",
                "--name-status",
            ]
            result = subprocess.run(
                cmd, cwd=self.local_path, capture_output=True, text=True, check=True
            )
            commits = []
            current_commit = None
            for line in result.stdout.splitlines():
                if line.startswith("COMMIT|"):
                    parts = line.split("|", 4)
                    current_commit = {
                        "hash": parts[1],
                        "author": parts[2],
                        "date": parts[3],
                        "message": parts[4],
                        "changes": [],
                    }
                    commits.append(current_commit)
                elif current_commit and line.strip():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        current_commit["changes"].append({"status": parts[0], "path": parts[1]})
            return commits
        except Exception as e:
            logger.error(f"Error getting commit log: {e}")
            return []
