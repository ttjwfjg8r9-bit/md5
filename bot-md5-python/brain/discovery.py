from typing import List, Dict, Any


def extract_streak(outcomes):
    if not outcomes:
        return "", 0
    last = outcomes[-1]
    streak = 1
    for i in range(len(outcomes) - 2, -1, -1):
        if outcomes[i] == last:
            streak += 1
        else:
            break
    return last, streak


def is_alternating(seq, min_len=6):
    if len(seq) < min_len:
        return False
    return all(seq[i] != seq[i - 1] for i in range(1, len(seq)))


def summarize_recent(outcomes, n=10):
    recent = outcomes[-n:] if outcomes else []
    tai = recent.count("TAI")
    return {
        "tai": tai,
        "xiu": len(recent) - tai,
        "tai_rate": tai / len(recent) if recent else 0.5,
        "last": recent[-1] if recent else None,
    }
