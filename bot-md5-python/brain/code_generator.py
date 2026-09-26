from typing import Dict, Any


def generate_module_variant(module: str, suggestion: str, acc: float) -> str:
    if module in ("deepseek", "deepseek.py"):
        if suggestion == "increase_score" or acc >= 0.56:
            return _deepseek_strong()
        return _deepseek_relax()
    if module in ("hybrid", "hybrid.py"):
        if acc >= 0.56:
            return _hybrid_strong()
        return _hybrid_relax()
    if module in ("soiCau", "soi_cau_pro", "soi_cau_pro.py"):
        if acc >= 0.56:
            return _soicau_strong()
        return _soicau_relax()
    return ""


def _deepseek_strong():
    return '''def analyze(history):
    if len(history) < 18: return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 15: return None
    t10 = outs[-10:].count("TAI")
    t15 = outs[-15:].count("TAI")
    if t10 >= 8: return {"pred": "XIU", "score": 3.5, "reason": "DeepSeek Evo: dao cuc"}
    if t10 <= 2: return {"pred": "TAI", "score": 3.5, "reason": "DeepSeek Evo: dao cuc"}
    if t10 >= 7: return {"pred": "XIU", "score": 2.9, "reason": "DeepSeek Evo: dao manh"}
    if t10 <= 3: return {"pred": "TAI", "score": 2.9, "reason": "DeepSeek Evo: dao manh"}
    if t15 >= 11: return {"pred": "XIU", "score": 2.3, "reason": "DeepSeek Evo: 15"}
    if t15 <= 4: return {"pred": "TAI", "score": 2.3, "reason": "DeepSeek Evo: 15"}
    return None
'''


def _deepseek_relax():
    return '''def analyze(history):
    if len(history) < 15: return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 12: return None
    t8 = outs[-8:].count("TAI")
    t10 = outs[-10:].count("TAI")
    if t8 >= 6: return {"pred": "XIU", "score": 2.8, "reason": "DeepSeek Evo: noi"}
    if t8 <= 2: return {"pred": "TAI", "score": 2.8, "reason": "DeepSeek Evo: noi"}
    if t10 >= 7: return {"pred": "XIU", "score": 2.3, "reason": "DeepSeek Evo: noi 10"}
    if t10 <= 3: return {"pred": "TAI", "score": 2.3, "reason": "DeepSeek Evo: noi 10"}
    return None
'''


def _hybrid_strong():
    return '''def analyze(history):
    if len(history) < 12: return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 8: return None
    last = outs[-1]
    streak = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: streak += 1
        else: break
    if streak >= 5: return {"pred": "XIU" if last == "TAI" else "TAI", "score": 3.2, "reason": f"Hybrid Evo: break {streak}"}
    if streak == 4: return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.4, "reason": "Hybrid Evo: break 4"}
    if streak == 2: return {"pred": last, "score": 2.1, "reason": "Hybrid Evo: follow 2"}
    return None
'''


def _hybrid_relax():
    return '''def analyze(history):
    if len(history) < 10: return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 6: return None
    last = outs[-1]
    streak = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: streak += 1
        else: break
    if streak >= 4: return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.8, "reason": f"Hybrid Evo: break noi {streak}"}
    if streak == 2: return {"pred": last, "score": 1.8, "reason": "Hybrid Evo: follow 2"}
    return None
'''


def _soicau_strong():
    return '''def analyze(history):
    if len(history) < 8: return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 8: return None
    last = outs[-1]
    streak = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: streak += 1
        else: break
    if streak >= 5: return {"pred": "XIU" if last == "TAI" else "TAI", "score": 3.4, "reason": f"SoiCau Evo: Be {streak}"}
    if streak == 2: return {"pred": last, "score": 2.0, "reason": "SoiCau Evo: Follow 2"}
    last6 = outs[-6:]
    if all(last6[i] != last6[i-1] for i in range(1, len(last6))):
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.6, "reason": "SoiCau Evo: 1-1"}
    return None
'''


def _soicau_relax():
    return '''def analyze(history):
    if len(history) < 6: return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 6: return None
    last = outs[-1]
    streak = 1
    for i in range(len(outs)-2, -1, -1):
        if outs[i] == last: streak += 1
        else: break
    if streak >= 4: return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.7, "reason": f"SoiCau Evo: Be noi {streak}"}
    if streak == 2: return {"pred": last, "score": 1.7, "reason": "SoiCau Evo: Follow 2"}
    return None
'''
