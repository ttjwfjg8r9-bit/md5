from pathlib import Path
from typing import Dict, List, Any
import ast

ROOT = Path(__file__).resolve().parent.parent
SAFE = [ROOT / "modules", ROOT / "brain", ROOT / "generated_algorithms"]
IMMUTABLE_NAMES = {".env", "secrets", "credentials", "token", "password"}


class CodeAnalyzer:
    def list_safe_files(self) -> List[Path]:
        files = []
        for d in SAFE:
            if not d.exists():
                continue
            for p in d.rglob("*.py"):
                if any(x in p.name.lower() for x in IMMUTABLE_NAMES):
                    continue
                files.append(p)
        return files

    def parse_file(self, path: Path) -> Dict[str, Any]:
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            return {
                "path": str(path),
                "funcs": funcs,
                "classes": classes,
                "lines": len(src.splitlines()),
                "ok": True,
            }
        except Exception as e:
            return {"path": str(path), "ok": False, "error": str(e)}

    def find_weakness(self, module_stats: Dict[str, Dict]) -> List[Dict]:
        weak = []
        for name, st in module_stats.items():
            total = st.get("hits", 0) + st.get("misses", 0)
            if total < 30:
                continue
            acc = st["hits"] / total
            if acc <= 0.48:
                weak.append({
                    "module": name,
                    "accuracy": round(acc, 4),
                    "samples": total,
                    "reason": "accuracy_below_048",
                    "suggestion": "relax_threshold" if acc > 0.42 else "tighten_or_disable",
                })
            elif acc >= 0.56 and total >= 50:
                weak.append({
                    "module": name,
                    "accuracy": round(acc, 4),
                    "samples": total,
                    "reason": "strong_can_promote_score",
                    "suggestion": "increase_score",
                })
        return weak
