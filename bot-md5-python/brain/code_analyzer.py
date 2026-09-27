from pathlib import Path
from typing import Dict, List, Any
import ast

ROOT = Path(__file__).resolve().parent.parent
SAFE = [ROOT / "modules", ROOT / "brain", ROOT / "generated_algorithms", ROOT / "learning", ROOT / "strategy", ROOT / "scoring"]
CONTROLLED = [ROOT / "config", ROOT / "server.py", ROOT / "index.js"]
IMMUTABLE_NAMES = {".env", "secrets", "credentials", "token", "password", "auth", "railway"}


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
            imports = [n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)]
            complexity = len(list(ast.walk(tree)))
            return {
                "path": str(path),
                "funcs": funcs,
                "classes": classes,
                "imports": imports,
                "lines": len(src.splitlines()),
                "complexity": complexity,
                "ok": True,
            }
        except Exception as e:
            return {"path": str(path), "ok": False, "error": str(e)}

    def classify_target(self, path: Path) -> str:
        rel = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
        if rel.startswith("modules/") or rel.startswith("brain/") or rel.startswith("generated_algorithms/"):
            return "SAFE_TO_EDIT"
        if rel.startswith("config/") or rel.endswith("server.py") or rel.endswith("index.js"):
            return "CONTROLLED"
        if any(token in rel.lower() for token in (".env", "token", "secret", "credential", "auth", "railway")):
            return "IMMUTABLE"
        return "SAFE_TO_EDIT"

    def analyze_module(self, path: Path) -> Dict[str, Any]:
        parsed = self.parse_file(path)
        if not parsed.get("ok"):
            return parsed
        return {
            **parsed,
            "allowlist": self.classify_target(path),
            "api_surface": {
                "funcs": parsed.get("funcs", []),
                "classes": parsed.get("classes", []),
            },
        }

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
