import importlib.util
from typing import Any, Dict, List

from .code_analyzer import CodeAnalyzer
from .code_generator import generate_module_variant
from .evolution_manager import EvolutionManager
from .patch_engine import PatchEngine
from .regression_tester import backtest_analyze, walk_forward
from .rollback_manager import RollbackManager
from .test_engine import TestEngine
from .git_manager import GitManager

MODULE_MAP = {
    "deepseek": "deepseek.py",
    "hybrid": "hybrid.py",
    "soiCau": "soi_cau_pro.py",
    "soi_cau_pro": "soi_cau_pro.py",
}


class SelfCodeEvolution:
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.patch = PatchEngine()
        self.manager = EvolutionManager()
        self.rollback = RollbackManager()
        self.test_engine = TestEngine()
        self.git_manager = GitManager()

    def _load_analyze_from_code(self, code: str):
        spec = importlib.util.spec_from_loader("evo_tmp", loader=None)
        mod = importlib.util.module_from_spec(spec)
        exec(code, mod.__dict__)
        return mod.analyze

    def run_once(self, history: List[dict], module_stats: Dict[str, Dict]) -> Dict[str, Any]:
        log = {"steps": []}
        if not self.manager.can_evolve():
            return {"status": "skipped", "reason": "max_evolutions_per_day"}

        weak = self.analyzer.find_weakness(module_stats)
        log["steps"].append({"ANALYZE": "ok", "weak": weak})
        if not weak:
            return {"status": "no_weakness", "log": log}

        target = min(weak, key=lambda x: x["accuracy"])
        mod_name = target["module"]
        file_name = MODULE_MAP.get(mod_name, f"{mod_name}.py")
        suggestion = target["suggestion"]
        acc = target["accuracy"]

        new_code = generate_module_variant(mod_name, suggestion, acc)
        if not new_code.strip():
            return {"status": "no_code", "log": log}
        log["steps"].append({"GENERATE": file_name, "suggestion": suggestion})

        try:
            fn = self._load_analyze_from_code(new_code)
        except Exception as e:
            return {"status": "compile_fail", "error": str(e), "log": log}

        bt = backtest_analyze(fn, history)
        log["steps"].append({"BACKTEST": bt})
        if not bt.get("ok") or not bt.get("pass"):
            self.manager.record({"result": "rejected", "stage": "backtest", "module": mod_name, "bt": bt})
            return {"status": "rejected_backtest", "log": log}

        wf = walk_forward(fn, history)
        log["steps"].append({"WALK_FORWARD": wf})
        if not wf.get("ok") or not wf.get("pass"):
            self.manager.record({"result": "rejected", "stage": "walk_forward", "module": mod_name, "wf": wf})
            return {"status": "rejected_walk_forward", "log": log}

        if wf["mean_accuracy"] + 0.02 < acc and acc >= 0.50:
            self.manager.record({"result": "rejected", "stage": "compare", "module": mod_name})
            return {"status": "rejected_compare", "log": log}

        applied = self.patch.apply(
            file_name,
            new_code,
            reason=f"{target['reason']} suggestion={suggestion} bt={bt.get('accuracy')} wf={wf.get('mean_accuracy')}",
            metrics={"backtest": bt, "walk_forward": wf, "before_acc": acc},
        )
        log["steps"].append({"APPLY": applied})
        if not applied.get("ok"):
            return {"status": "apply_fail", "log": log}

        validation = self.test_engine.validate_candidate(new_code, history)
        log["steps"].append({"VALIDATION": validation})
        if not validation.get("ok"):
            self.rollback.rollback_last(file_name)
            self.manager.record({
                "result": "rollback",
                "module": mod_name,
                "file": file_name,
                "validation": validation,
            })
            return {"status": "rollback", "log": log, "validation": validation}

        git_status = self.git_manager.commit_and_push(f"AI Evolution v{self.manager.data.get('history',[]).__len__() + 1}: {file_name}")
        log["steps"].append({"GIT": git_status})

        self.manager.record({
            "result": "accepted",
            "module": mod_name,
            "file": file_name,
            "backtest": bt,
            "walk_forward": wf,
            "validation": validation,
            "git": git_status,
            "slot": applied.get("slot"),
        })
        self.manager.record_evolution(
            version=f"v{len(self.manager.data.get('history', [])) + 1}",
            change=f"modify_{file_name}",
            reason=f"{target['reason']} recommendation={suggestion}",
            before_metrics={"accuracy": acc},
            after_metrics={"backtest": bt.get("accuracy"), "walk_forward": wf.get("mean_accuracy")},
            result="accepted",
            lessons=["validated_with_backtest_and_walk_forward", "committed_and_pushed_if_possible"],
        )
        print(f"[EVO] APPLIED {file_name} bt={bt.get('accuracy')} wf={wf.get('mean_accuracy')}")
        return {"status": "applied", "log": log, "applied": applied, "git": git_status}
