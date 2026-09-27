"""
Deep pipeline:
feature search -> top candidate -> generate code -> validate -> backtest
-> walk_forward (noi) -> patch module yeu nhat / hoac ghi generated_algorithms/
"""
from typing import Dict, List, Any
import importlib.util
from pathlib import Path

from .feature_engine import search_candidates
from .code_generator_deep import generate_analyze_from_rule
from .patch_engine import PatchEngine
from .regression_tester import backtest_analyze, walk_forward
from .evolution_manager import EvolutionManager

ROOT = Path(__file__).resolve().parent.parent
GEN_DIR = ROOT / "generated_algorithms"
GEN_DIR.mkdir(exist_ok=True)

MODULE_MAP = {
    "deepseek": "deepseek.py",
    "hybrid": "hybrid.py",
    "soiCau": "soi_cau_pro.py",
}


class DeepSelfCodeEvolution:
    def __init__(self):
        self.patch = PatchEngine()
        self.manager = EvolutionManager()

    def _load_fn(self, code: str):
        spec = importlib.util.spec_from_loader("deep_evo_tmp", loader=None)
        mod = importlib.util.module_from_spec(spec)
        exec(code, mod.__dict__)
        return mod.analyze

    def run_once(self, history: List[dict], module_stats: Dict[str, Dict] = None) -> Dict[str, Any]:
        log = {"steps": []}
        if not self.manager.can_evolve():
            return {"status": "skipped", "reason": "max_per_day"}

        if len(history) < 80:
            return {"status": "need_more_history", "n": len(history)}

        candidates = search_candidates(history, min_signals=20)
        log["steps"].append({"SEARCH": f"{len(candidates)} candidates"})
        if not candidates:
            return {"status": "no_candidate", "log": log}

        best = candidates[0]
        log["steps"].append({
            "BEST": best["name"],
            "acc": best["accuracy"],
            "n": best["samples"],
        })
        print(f"[DEEP-EVO] best={best['name']} acc={best['accuracy']:.1%} n={best['samples']}")

        code = generate_analyze_from_rule(best["name"], best.get("score", 2.5))
        try:
            fn = self._load_fn(code)
        except Exception as e:
            return {"status": "compile_fail", "error": str(e), "log": log}

        bt = backtest_analyze(fn, history)
        log["steps"].append({"BACKTEST": bt})
        if not bt.get("ok") or not bt.get("pass"):
            self.manager.record({"result": "rejected", "stage": "backtest", "cand": best["name"]})
            return {"status": "rejected_backtest", "log": log, "bt": bt}

        wf = walk_forward(fn, history)
        log["steps"].append({"WALK_FORWARD": wf})
        if not wf.get("ok"):
            self.manager.record({"result": "rejected", "stage": "walk_forward", "cand": best["name"]})
            return {"status": "rejected_walk_forward", "log": log, "wf": wf}
        if wf.get("mean_accuracy", 0) < 0.45:
            self.manager.record({"result": "rejected", "stage": "walk_forward_low", "cand": best["name"]})
            return {"status": "rejected_walk_forward", "log": log, "wf": wf}

        path = GEN_DIR / f"algo_{best['name']}.py"
        path.write_text(code, encoding="utf-8")
        log["steps"].append({"SAVED": str(path)})

        target_module = None
        if module_stats:
            weak = []
            for name, st in module_stats.items():
                t = st.get("hits", 0) + st.get("misses", 0)
                if t >= 20:
                    weak.append((name, st["hits"] / t if t else 0))
            if weak:
                weak.sort(key=lambda x: x[1])
                target_module = MODULE_MAP.get(weak[0][0])

        applied = None
        if target_module:
            applied = self.patch.apply(
                target_module,
                code,
                reason=f"DeepEvo {best['name']} acc={best['accuracy']} bt={bt.get('accuracy')} wf={wf.get('mean_accuracy')}",
                metrics={"candidate": best, "backtest": bt, "walk_forward": wf},
            )
            log["steps"].append({"PATCH": applied})

        self.manager.record({
            "result": "accepted" if (applied and applied.get("ok")) else "saved_only",
            "candidate": best["name"],
            "accuracy": best["accuracy"],
            "backtest": bt,
            "walk_forward": wf,
        })
        status = "applied" if (applied and applied.get("ok")) else "saved_generated"
        print(f"[DEEP-EVO] {status} {best['name']}")
        return {"status": status, "log": log, "best": best, "applied": applied}
