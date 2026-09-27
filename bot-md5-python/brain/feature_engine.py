"""Trich feature tu history de tim algorithm moi."""
from typing import List, Dict, Any, Optional
from collections import Counter
import math


def outcomes(history: List[dict]) -> List[str]:
    return [h["outcome"] for h in history if h.get("outcome") in ("TAI", "XIU")]


def streak(outs: List[str]) -> int:
    if not outs:
        return 0
    last = outs[-1]
    n = 1
    for i in range(len(outs) - 2, -1, -1):
        if outs[i] == last:
            n += 1
        else:
            break
    return n


def is_alt(seq: List[str]) -> bool:
    if len(seq) < 4:
        return False
    return all(seq[i] != seq[i - 1] for i in range(1, len(seq)))


def entropy(seq: List[str]) -> float:
    if not seq:
        return 0.0
    c = Counter(seq)
    n = len(seq)
    e = 0.0
    for v in c.values():
        p = v / n
        e -= p * math.log2(p)
    return e


def extract_features(history: List[dict]) -> Dict[str, Any]:
    outs = outcomes(history)
    if len(outs) < 10:
        return {}
    last = outs[-1]
    opp = "XIU" if last == "TAI" else "TAI"
    st = streak(outs)
    last5 = outs[-5:]
    last10 = outs[-10:]
    last15 = outs[-15:] if len(outs) >= 15 else outs
    t5 = last5.count("TAI")
    t10 = last10.count("TAI")
    t15 = last15.count("TAI")
    # transition
    trans_same = 0
    trans_flip = 0
    for i in range(1, min(20, len(outs))):
        if outs[-i] == outs[-i - 1] if len(outs) > i else False:
            trans_same += 1
        else:
            trans_flip += 1
    return {
        "last": last,
        "opp": opp,
        "streak": st,
        "t5": t5,
        "t10": t10,
        "t15": t15,
        "x5": 5 - t5,
        "x10": len(last10) - t10,
        "alt6": is_alt(outs[-6:]),
        "alt8": is_alt(outs[-8:]) if len(outs) >= 8 else False,
        "entropy10": round(entropy(last10), 3),
        "entropy15": round(entropy(last15), 3),
        "ratio10": t10 / max(len(last10), 1),
        "flip_ratio": trans_flip / max(trans_same + trans_flip, 1),
    }


def _rules():
    def r(name, cond, pred, score):
        return {"name": name, "cond": cond, "pred": pred, "score": score}

    return [
        r("break_streak_5", lambda f: f.get("streak", 0) >= 5, lambda f: f["opp"], 3.2),
        r("break_streak_4", lambda f: f.get("streak", 0) == 4, lambda f: f["opp"], 2.5),
        r("follow_streak_2", lambda f: f.get("streak", 0) == 2, lambda f: f["last"], 2.0),
        r("follow_streak_3", lambda f: f.get("streak", 0) == 3, lambda f: f["last"], 1.8),
        r("dao_t10_high", lambda f: f.get("t10", 0) >= 8, lambda f: "XIU", 3.4),
        r("dao_t10_low", lambda f: f.get("t10", 0) <= 2, lambda f: "TAI", 3.4),
        r("dao_t10_7", lambda f: f.get("t10", 0) >= 7, lambda f: "XIU", 2.8),
        r("dao_t10_3", lambda f: f.get("t10", 0) <= 3, lambda f: "TAI", 2.8),
        r("dao_t15_high", lambda f: f.get("t15", 0) >= 11, lambda f: "XIU", 2.6),
        r("dao_t15_low", lambda f: f.get("t15", 0) <= 4, lambda f: "TAI", 2.6),
        r("alt6", lambda f: f.get("alt6"), lambda f: f["opp"], 2.4),
        r("alt8", lambda f: f.get("alt8"), lambda f: f["opp"], 2.7),
        r("low_entropy_follow", lambda f: f.get("entropy10", 1) < 0.7 and f.get("streak", 0) >= 2, lambda f: f["last"], 2.1),
        r("high_entropy_break", lambda f: f.get("entropy10", 0) > 0.95 and f.get("streak", 0) >= 3, lambda f: f["opp"], 2.2),
        r("flip_heavy", lambda f: f.get("flip_ratio", 0) > 0.65 and f.get("streak", 0) == 1, lambda f: f["opp"], 1.9),
        r("ratio10_extreme_hi", lambda f: f.get("ratio10", 0.5) >= 0.8, lambda f: "XIU", 3.0),
        r("ratio10_extreme_lo", lambda f: f.get("ratio10", 0.5) <= 0.2, lambda f: "TAI", 3.0),
    ]


def search_candidates(history: List[dict], min_signals: int = 25) -> List[Dict[str, Any]]:
    """Walk history, score moi rule, tra ve candidate tot."""
    outs_full = outcomes(history)
    n = len(outs_full)
    if n < min_signals + 15:
        return []

    stats = {r["name"]: {"hits": 0, "misses": 0, "rule": r} for r in _rules()}

    for i in range(15, n):
        sub = [{"outcome": o} for o in outs_full[:i]]
        feat = extract_features(sub)
        if not feat:
            continue
        actual = outs_full[i]
        for r in _rules():
            try:
                if not r["cond"](feat):
                    continue
                pred = r["pred"](feat)
                if pred == actual:
                    stats[r["name"]]["hits"] += 1
                else:
                    stats[r["name"]]["misses"] += 1
            except Exception:
                continue

    results = []
    for name, st in stats.items():
        total = st["hits"] + st["misses"]
        if total < min_signals:
            continue
        acc = st["hits"] / total
        if acc < 0.52:
            continue
        results.append({
            "name": name,
            "accuracy": round(acc, 4),
            "samples": total,
            "hits": st["hits"],
            "misses": st["misses"],
            "score": st["rule"]["score"],
            "rule": st["rule"],
        })
    results.sort(key=lambda x: (x["accuracy"], x["samples"]), reverse=True)
    return results
