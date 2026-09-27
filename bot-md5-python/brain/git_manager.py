import os
import subprocess
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent


class GitManager:
    """Thin wrapper for commit/push operations with environment-variable based auth."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or ROOT

    def git(self, *args: str) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "ok": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def configured(self) -> bool:
        env_tokens = [
            "GITHUB_TOKEN",
            "GH_TOKEN",
            "GIT_TOKEN",
            "GIT_AUTHOR_NAME",
            "GIT_AUTHOR_EMAIL",
        ]
        has_any = any(os.getenv(k) for k in env_tokens)
        remote = self.git("remote", "-v")
        return has_any or remote.get("ok", False)

    def commit_and_push(self, message: str, branch: str = "main") -> Dict[str, Any]:
        if not self.configured():
            return {"ok": False, "status": "not_configured", "message": "Missing Git credentials or remote"}

        status = self.git("status", "--short")
        if not status.get("ok", False):
            return {"ok": False, "status": "git_error", **status}
        if not status.get("stdout"):
            return {"ok": False, "status": "nothing_to_commit", "message": "No git changes"}

        add = self.git("add", ".")
        if not add.get("ok", False):
            return {"ok": False, "status": "git_add_failed", **add}

        commit = self.git("commit", "-m", message)
        if not commit.get("ok", False):
            if "nothing to commit" in (commit.get("stdout") + commit.get("stderr", "")).lower():
                return {"ok": False, "status": "nothing_to_commit", **commit}
            return {"ok": False, "status": "git_commit_failed", **commit}

        push = self.git("push", "origin", f"HEAD:{branch}")
        if not push.get("ok", False):
            return {"ok": False, "status": "git_push_failed", **push}

        return {"ok": True, "status": "pushed", "message": message, **push}
