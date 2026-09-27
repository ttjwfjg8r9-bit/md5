import ast
import importlib.util
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from .regression_tester import backtest_analyze, walk_forward

ROOT = Path(__file__).resolve().parent.parent


class TestEngine:
    """Realtime validation layer: syntax, import, backtest, walk-forward, shadow checks."""

    def __init__(self):
        self.root = ROOT

    def syntax_ok(self, code: str) -> Dict[str, Any]:
        try:
            ast.parse(code)
            return {"ok": True, "message": "syntax_ok"}
        except Exception as e:
            return {"ok": False, "message": str(e), "error": traceback.format_exc()}

    def import_ok(self, code: str, module_name: str = "evo_test_tmp") -> Dict[str, Any]:
        try:
            spec = importlib.util.spec_from_loader(module_name, loader=None)
            mod = importlib.util.module_from_spec(spec)
            exec(code, mod.__dict__)
            fn = getattr(mod, "analyze", None)
            if not callable(fn):
                return {"ok": False, "message": "missing_analyze"}
            return {"ok": True, "message": "import_ok"}
        except Exception as e:
            return {"ok": False, "message": str(e), "error": traceback.format_exc()}

    def validate_candidate(self, code: str, history: List[dict], module_name: str = "evo_test_tmp") -> Dict[str, Any]:
        syntax = self.syntax_ok(code)
        if not syntax["ok"]:
            return {"ok": False, "stage": "syntax", **syntax}

        import_check = self.import_ok(code, module_name)
        if not import_check["ok"]:
            return {"ok": False, "stage": "import", **import_check}

        spec = importlib.util.spec_from_loader(module_name, loader=None)
        mod = importlib.util.module_from_spec(spec)
        exec(code, mod.__dict__)
        fn = mod.analyze

        backtest = backtest_analyze(fn, history)
        if not backtest.get("ok"):
            return {"ok": False, "stage": "backtest", **backtest}

        walk = walk_forward(fn, history)
        if not walk.get("ok"):
            return {"ok": False, "stage": "walk_forward", **walk}

        shadow_pass = backtest.get("pass", False) and walk.get("pass", False)
        return {
            "ok": shadow_pass,
            "stage": "shadow",
            "syntax": syntax,
            "import_check": import_check,
            "backtest": backtest,
            "walk_forward": walk,
            "shadow_pass": shadow_pass,
        }

    def shadow_run(self, code: str, history: List[dict], module_name: str = "evo_shadow_tmp") -> Dict[str, Any]:
        result = self.validate_candidate(code, history, module_name)
        if result.get("ok"):
            result["status"] = "shadow"
        else:
            result["status"] = "rejected"
        return result
