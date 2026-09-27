"""Sinh source Python that tu candidate rule."""


def generate_analyze_from_rule(rule_name: str, score: float) -> str:
    """Map rule name -> code analyze()."""
    templates = {
        "break_streak_5": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 8: return None
    last = outs[-1]
    st = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: st += 1
        else: break
    if st >= 5:
        return {{"pred": "XIU" if last == "TAI" else "TAI", "score": {score}, "reason": "DeepEvo: break_streak_5"}}
    return None
''',
        "break_streak_4": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 6: return None
    last = outs[-1]
    st = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: st += 1
        else: break
    if st == 4:
        return {{"pred": "XIU" if last == "TAI" else "TAI", "score": {score}, "reason": "DeepEvo: break_streak_4"}}
    return None
''',
        "follow_streak_2": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 5: return None
    last = outs[-1]
    st = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: st += 1
        else: break
    if st == 2:
        return {{"pred": last, "score": {score}, "reason": "DeepEvo: follow_2"}}
    return None
''',
        "dao_t10_high": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    if outs[-10:].count("TAI") >= 8:
        return {{"pred": "XIU", "score": {score}, "reason": "DeepEvo: dao_t10_high"}}
    return None
''',
        "dao_t10_low": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    if outs[-10:].count("TAI") <= 2:
        return {{"pred": "TAI", "score": {score}, "reason": "DeepEvo: dao_t10_low"}}
    return None
''',
        "dao_t10_7": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    if outs[-10:].count("TAI") >= 7:
        return {{"pred": "XIU", "score": {score}, "reason": "DeepEvo: dao_t10_7"}}
    return None
''',
        "dao_t10_3": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    if outs[-10:].count("TAI") <= 3:
        return {{"pred": "TAI", "score": {score}, "reason": "DeepEvo: dao_t10_3"}}
    return None
''',
        "alt6": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 8: return None
    last6 = outs[-6:]
    if all(last6[i] != last6[i-1] for i in range(1, 6)):
        last = outs[-1]
        return {{"pred": "XIU" if last == "TAI" else "TAI", "score": {score}, "reason": "DeepEvo: alt6"}}
    return None
''',
        "alt8": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 10: return None
    last8 = outs[-8:]
    if all(last8[i] != last8[i-1] for i in range(1, 8)):
        last = outs[-1]
        return {{"pred": "XIU" if last == "TAI" else "TAI", "score": {score}, "reason": "DeepEvo: alt8"}}
    return None
''',
        "ratio10_extreme_hi": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    if outs[-10:].count("TAI") / 10 >= 0.8:
        return {{"pred": "XIU", "score": {score}, "reason": "DeepEvo: ratio_hi"}}
    return None
''',
        "ratio10_extreme_lo": f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    if outs[-10:].count("TAI") / 10 <= 0.2:
        return {{"pred": "TAI", "score": {score}, "reason": "DeepEvo: ratio_lo"}}
    return None
''',
    }
    code = templates.get(rule_name)
    if code:
        return code
    return f'''def analyze(history):
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 10: return None
    last = outs[-1]
    st = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: st += 1
        else: break
    if st >= 5:
        return {{"pred": "XIU" if last == "TAI" else "TAI", "score": {score}, "reason": "DeepEvo: {rule_name}"}}
    return None
'''
