import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "memory" / "evolution_memory.json"
MAX_PER_DAY = 5
MAX_CODE_CHANGES = 20
MAX_ROLLBACKS = 5


class EvolutionManager:
    def __init__(self):
        self.data = {"events": [], "daily": {}, "history": [], "meta_learning": []}
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

    def record_evolution(self, version: str, change: str, reason: str, before_metrics: dict, after_metrics: dict, result: str, lessons: list):
        entry = {
            "version": version,
            "change": change,
            "reason": reason,
            "before_metrics": before_metrics,
            "after_metrics": after_metrics,
            "result": result,
            "lessons": lessons,
            "time": time.time(),
        }
        self.data.setdefault("history", []).append(entry)
        self.data["history"] = self.data["history"][-500:]
        self.save()

    def get_recent_lessons(self, limit: int = 10):
        history = self.data.get("history", [])
        lessons = []
        for item in reversed(history[-limit:]):
            for lesson in item.get("lessons", []):
                lessons.append(lesson)
        return lessons

    def record_meta_learning(self, category: str, result: str, metrics: dict, lessons: list):
        if not isinstance(lessons, list):
            lessons = [str(lessons)]
        entry = {
            "category": category,
            "result": result,
            "metrics": metrics or {},
            "lessons": lessons,
            "time": time.time(),
        }
        existing = self.data.setdefault("meta_learning", [])
        existing.append(entry)
        self.data["meta_learning"] = existing[-200:]
        self.save()

    def get_meta_learning(self, limit: int = 10):
        entries = self.data.get("meta_learning", [])
        return list(reversed(entries[-limit:]))

    def should_retry(self, change_name: str, max_repeat: int = 2) -> bool:
        history = self.data.get("history", [])
        count = 0
        for item in reversed(history):
            if item.get("change") == change_name:
                count += 1
                if count >= max_repeat:
                    return False
        return True
