import os
import subprocess


class GitHubSync:
    def __init__(self):
        self.enabled = os.getenv("AUTO_GIT_PUSH", "false").lower() == "true"

    def run(self, command):
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "git command failed")
        return result.stdout

    def sync(self, message):
        if not self.enabled:
            return {"status": "disabled"}

        try:
            self.run("git config user.name 'Brain Auto Evolution'")
            self.run("git config user.email 'brain@localhost'")
            self.run("git add generated/ memory/")

            status = self.run("git status --porcelain")
            if not status.strip():
                return {"status": "nothing_to_commit"}

            safe_msg = message.replace('"', "'")[:120]
            self.run(f'git commit -m "{safe_msg}"')
            self.run("git push origin HEAD")

            return {"status": "pushed", "message": safe_msg}
        except Exception as e:
            print(f"GitHub sync loi: {e}")
            return {"status": "error", "error": str(e)}
