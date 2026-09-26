import json
import shutil
from datetime import datetime
from pathlib import Path

from .code_validator import validate_has_analyze, validate_syntax

ROOT = Path(__file__).resolve().parent.parent
MODULES = ROOT / "modules"
HISTORY = ROOT / "evolution_history"
HISTORY.mkdir(exist_ok=True)

ALLOW = {"deepseek.py", "hybrid.py", "soi_cau_pro.py", "markov_dice.py"}


class PatchEngine:
    def apply(self, module_file: str, new_code: str, reason: str, metrics: dict) -> dict:
        if module_file not in ALLOW:
            return {"ok": False, "error": "not_in_allowlist"}

        ok, msg = validate_syntax(new_code)
        if not ok:
            return {"ok": False, "error": f"syntax: {msg}"}
        ok, msg = validate_has_analyze(new_code)
        if not ok:
            return {"ok": False, "error": msg}

        target = MODULES / module_file
        if not target.exists():
            return {"ok": False, "error": "file_missing"}

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slot = HISTORY / f"evo_{ts}_{module_file.replace('.py', '')}"
        slot.mkdir(parents=True)
        before = target.read_text(encoding="utf-8")
        (slot / "before.py").write_text(before, encoding="utf-8")
        (slot / "after.py").write_text(new_code, encoding="utf-8")
        (slot / "reason.txt").write_text(reason, encoding="utf-8")
        (slot / "metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        bak = ROOT / "generated" / "backups" / f"{module_file}.{ts}.bak"
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, bak)

        target.write_text(new_code, encoding="utf-8")
        return {
            "ok": True,
            "slot": str(slot),
            "backup": str(bak),
            "module": module_file,
        }
