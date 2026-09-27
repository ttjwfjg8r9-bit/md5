import json
import shutil
from datetime import datetime
from pathlib import Path

from .code_validator import validate_has_analyze, validate_syntax

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"
BRAIN = ROOT / "brain"
HISTORY = ROOT / "evolution_history"
HISTORY.mkdir(exist_ok=True)

SAFE_TO_EDIT = {"deepseek.py", "hybrid.py", "soi_cau_pro.py", "markov_dice.py"}
CONTROLLED = {"server.py", "index.js", "config"}
IMMUTABLE = {".env", "credentials", "secrets", "auth", "token", "railway"}
ALLOW = SAFE_TO_EDIT | {"brain_core.py", "evolution.py", "self_code_evolution.py", "code_generator.py", "patch_engine.py"}


class PatchEngine:
    def classify(self, module_file: str) -> str:
        lowered = module_file.lower()
        if any(token in lowered for token in IMMUTABLE):
            return "IMMUTABLE"
        if module_file in SAFE_TO_EDIT or module_file in ALLOW:
            return "SAFE_TO_EDIT"
        if any(item in lowered for item in ("server.py", "index.js", "config")):
            return "CONTROLLED"
        return "SAFE_TO_EDIT"

    def is_allowed_target(self, module_file: str) -> bool:
        status = self.classify(module_file)
        return status in {"SAFE_TO_EDIT", "CONTROLLED"} and module_file not in {".env", "settings.py"}

    def apply(self, module_file: str, new_code: str, reason: str, metrics: dict) -> dict:
        status = self.classify(module_file)
        if status == "IMMUTABLE":
            return {"ok": False, "error": "immutable_target"}
        if not self.is_allowed_target(module_file):
            return {"ok": False, "error": "not_in_allowlist"}

        ok, msg = validate_syntax(new_code)
        if not ok:
            return {"ok": False, "error": f"syntax: {msg}"}
        ok, msg = validate_has_analyze(new_code)
        if not ok:
            return {"ok": False, "error": msg}

        target = (MODULES / module_file) if (MODULES / module_file).exists() else (BRAIN / module_file)
        if not target.exists():
            return {"ok": False, "error": "file_missing"}

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slot = HISTORY / f"evo_{ts}_{module_file.replace('.py', '')}"
        slot.mkdir(parents=True)
        before = target.read_text(encoding="utf-8")
        (slot / "before.py").write_text(before, encoding="utf-8")
        (slot / "after.py").write_text(new_code, encoding="utf-8")
        (slot / "reason.txt").write_text(reason, encoding="utf-8")
        (slot / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        (slot / "diff.patch").write_text(f"--- before\n+++ after\n\n{before[:400]}\n---\n{new_code[:400]}\n", encoding="utf-8")

        bak = ROOT / "generated" / "backups" / f"{module_file}.{ts}.bak"
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, bak)

        target.write_text(new_code, encoding="utf-8")
        return {
            "ok": True,
            "slot": str(slot),
            "backup": str(bak),
            "module": module_file,
            "classification": status,
        }
