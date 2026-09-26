import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "memory" / "evolution_memory.json"
MAX_PER_DAY = 5


class EvolutionManager:
    def __init__(self):
        self.data = {"events": [], "daily": {}}
        self.load()

    def load(self):
        if MEM.exists():
            try:
                self.data = json.loads(MEM.read_text(encoding="utf-8"))
            except Exception:
                pass

    def save(self):
        MEM.parent.mkdir(exist_ok=True)
        MEM.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def can_evolve(self) -> bool:
        day = time.strftime("%Y-%m-%d")
        c = self.data.setdefault("daily", {}).get(day, 0)
        return c < MAX_PER_DAY

    def record(self, event: dict):
        day = time.strftime("%Y-%m-%d")
        self.data.setdefault("daily", {})
        self.data["daily"][day] = self.data["daily"].get(day, 0) + 1
        self.data.setdefault("events", []).append({**event, "time": time.time()})
        self.data["events"] = self.data["events"][-200:]
        self.save()
