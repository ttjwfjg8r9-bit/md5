from brain.evolution_manager import EvolutionManager
from brain.patch_engine import PatchEngine


def test_patch_engine_rejects_settings_file():
    result = PatchEngine().apply(
        "settings.py",
        "def analyze(history):\n    return {'pred': 'TAI', 'score': 1.2}\n",
        "unsafe mutation test",
        {},
    )
    assert result["ok"] is False
    assert "not_in_allowlist" in result["error"] or "immutable_target" in result["error"]


def test_evolution_manager_records_meta_learning():
    manager = EvolutionManager()
    manager.record_meta_learning(
        "shadow",
        "shadow_rejected",
        {"stage": "walk_forward", "mean_accuracy": 0.41},
        ["skip weak candidates", "keep real-signal only"],
    )
    history = manager.get_meta_learning(limit=5)
    assert history
    assert history[-1]["category"] == "shadow"
    assert "skip weak candidates" in history[-1]["lessons"]
