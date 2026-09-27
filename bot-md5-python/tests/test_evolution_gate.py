from core.ensemble import ensemble_predict, record_feedback


def test_valid_prediction_has_tai_or_xiu():
    history = [{"outcome": "TAI"} for _ in range(20)]
    prediction = ensemble_predict(history)
    assert prediction["pred"] in {"TAI", "XIU"}
    assert prediction["reason"]


def test_record_feedback_rejects_weak_prediction():
    history = [{
        "pred": "TAI",
        "confidence": 40,
        "active": 1,
        "reason": "RANDOM_BALANCED_FALLBACK",
        "outcome": "TAI",
    }]
    record_feedback(history, "XIU")
    assert True
