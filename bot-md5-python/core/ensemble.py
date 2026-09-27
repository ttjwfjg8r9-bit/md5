from typing import List, Dict, Any

from brain import Brain

_module_stats = {
    "deepseek": {"hits": 0, "misses": 0},
    "hybrid": {"hits": 0, "misses": 0},
    "soiCau": {"hits": 0, "misses": 0},
}

MIN_ACCEPT_CONFIDENCE = 55
MIN_ACTIVE_MODULES = 2


def note_module(name, correct):
    if name not in _module_stats:
        return
    if correct:
        _module_stats[name]["hits"] += 1
    else:
        _module_stats[name]["misses"] += 1


def get_module_stats():
    return _module_stats

try:
    from modules.deepseek import analyze as deepseek_analyze
except Exception:
    deepseek_analyze = None

try:
    from modules.hybrid import analyze as hybrid_analyze
except Exception:
    hybrid_analyze = None

try:
    from modules.markov_dice import analyze as markov_analyze
except Exception:
    markov_analyze = None

try:
    from modules.soi_cau_pro import analyze as soi_cau_analyze
except Exception:
    soi_cau_analyze = None

brain = Brain()

WEIGHTS = {
    "brain": 2.20,
    "deepseek": 1.60,
    "hybrid": 1.45,
    "markov": 1.40,
    "soiCau": 1.45,
}


def _outcomes(history):
    return [h["outcome"] for h in history if h.get("outcome")]


def ensemble_predict(history):
    if len(history) < 10:
        return {
            "pred": None,
            "confidence": 0,
            "reason": f"Warmup {len(history)}/10",
            "active": 0,
        }

    outs = _outcomes(history)
    scores = {"TAI": 0.0, "XIU": 0.0}
    reasons = []
    active = 0
    signals = []

    try:
        br = brain.think(outs)
        if br and br.get("pred"):
            w = WEIGHTS["brain"]
            s = float(br.get("score", 1.5)) * w
            scores[br["pred"]] += s
            reasons.append(br.get("reason", "Brain"))
            signals.append({"name": "brain", **br})
            active += 1
    except Exception as e:
        print("Brain loi:", e)

    helpers = [
        ("deepseek", deepseek_analyze),
        ("hybrid", hybrid_analyze),
        ("markov", markov_analyze),
        ("soiCau", soi_cau_analyze),
    ]
    for name, fn in helpers:
        if fn is None:
            continue
        try:
            res = fn(history)
            if not res or not res.get("pred"):
                continue
            w = WEIGHTS.get(name, 1.0)
            s = float(res.get("score", 1.0)) * w
            scores[res["pred"]] += s
            reasons.append(res.get("reason", name))
            signals.append({"name": name, **res})
            active += 1
        except Exception as e:
            print(f"Module {name} loi:", e)

    if scores["TAI"] == 0 and scores["XIU"] == 0:
        recent = outs[-6:]
        tai = recent.count("TAI")
        if tai >= 4:
            pred = "XIU"
        elif tai <= 2:
            pred = "TAI"
        else:
            pred = "XIU" if outs[-1] == "TAI" else "TAI"
        return {
            "pred": pred,
            "confidence": 50,
            "reason": "RANDOM_BALANCED_FALLBACK",
            "active": 0,
            "signals": [],
        }

    pred = "TAI" if scores["TAI"] > scores["XIU"] else "XIU"
    diff = abs(scores["TAI"] - scores["XIU"])
    conf = min(50 + diff * 6 + active * 2.5, 90)

    if active < MIN_ACTIVE_MODULES and conf < MIN_ACCEPT_CONFIDENCE:
        pred = "TAI" if len(outs) % 2 == 0 else "XIU"
        conf = 52
        reason = "RANDOM_BALANCED_FALLBACK"
    else:
        reason = " | ".join(reasons[:3]) + f" | {active} modules"

    return {
        "pred": pred,
        "confidence": round(conf),
        "reason": reason,
        "active": active,
        "scores": scores,
        "signals": signals,
        "brain_stats": brain.stats(),
    }


def record_feedback(history, actual):
    if not history or not history[-1].get("pred"):
        return

    reason = (history[-1].get("reason") or "").lower()
    confidence = int(history[-1].get("confidence") or 0)
    active = int(history[-1].get("active") or 0)

    if "warmup" in reason or "fallback" in reason:
        return
    if confidence < MIN_ACCEPT_CONFIDENCE or active < MIN_ACTIVE_MODULES:
        return

    outs = _outcomes(history)
    brain.learn(outs, actual)

    if history[-1].get("reason"):
        correct = history[-1].get("pred") == actual
        if "deepseek" in reason:
            note_module("deepseek", correct)
        if "hybrid" in reason:
            note_module("hybrid", correct)
        if "soicau" in reason or "soi cau" in reason:
            note_module("soiCau", correct)
