from typing import Any, Callable, Dict, List


def backtest_analyze(analyze_fn: Callable, history: List[dict], min_len: int = 20) -> Dict[str, Any]:
    if len(history) < min_len + 5:
        return {"ok": False, "reason": "not_enough_data", "n": len(history)}

    hits = misses = 0
    for i in range(min_len, len(history)):
        window = history[:i]
        actual = history[i].get("outcome")
        if actual not in ("TAI", "XIU"):
            continue
        try:
            res = analyze_fn(window)
        except Exception as e:
            return {"ok": False, "reason": f"runtime: {e}"}
        if not res or not res.get("pred"):
            continue
        if res["pred"] == actual:
            hits += 1
        else:
            misses += 1

    total = hits + misses
    if total < 15:
        return {"ok": False, "reason": "too_few_signals", "total": total}
    acc = hits / total
    return {
        "ok": True,
        "hits": hits,
        "misses": misses,
        "total": total,
        "accuracy": round(acc, 4),
        "pass": acc >= 0.48,
    }


def walk_forward(analyze_fn: Callable, history: List[dict], folds: int = 3) -> Dict[str, Any]:
    n = len(history)
    if n < 60:
        return {"ok": False, "reason": "need_60_plus"}
    fold_size = n // (folds + 1)
    accs = []
    for f in range(folds):
        train_end = fold_size * (f + 1)
        test_end = min(n, train_end + fold_size)
        hits = misses = 0
        for i in range(train_end, test_end):
            window = history[:i]
            actual = history[i].get("outcome")
            if actual not in ("TAI", "XIU"):
                continue
            try:
                res = analyze_fn(window)
            except Exception:
                continue
            if not res or not res.get("pred"):
                continue
            if res["pred"] == actual:
                hits += 1
            else:
                misses += 1
        t = hits + misses
        if t >= 8:
            accs.append(hits / t)
    if not accs:
        return {"ok": False, "reason": "no_fold_stats"}
    mean_acc = sum(accs) / len(accs)
    return {
        "ok": True,
        "fold_accuracies": [round(a, 4) for a in accs],
        "mean_accuracy": round(mean_acc, 4),
        "pass": mean_acc >= 0.45 and min(accs) >= 0.40,
    }
