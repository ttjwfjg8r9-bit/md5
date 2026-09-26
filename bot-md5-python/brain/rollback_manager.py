from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / "evolution_history"
MODULES = ROOT / "modules"


class RollbackManager:
    def list_slots(self):
        if not HISTORY.exists():
            return []
        return sorted([p for p in HISTORY.iterdir() if p.is_dir()], reverse=True)

    def rollback_last(self, module_file: str) -> dict:
        for slot in self.list_slots():
            before = slot / "before.py"
            if not before.exists():
                continue
            if module_file.replace(".py", "") not in slot.name:
                continue
            target = MODULES / module_file
            shutil.copy2(before, target)
            return {"ok": True, "restored_from": str(slot)}
        return {"ok": False, "error": "no_backup_slot"}
