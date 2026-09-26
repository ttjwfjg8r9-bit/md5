import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain import Brain


def test_brain_learn_and_predict():
    brain = Brain()
    hist = ["TAI", "TAI", "XIU", "TAI", "XIU", "XIU", "TAI"]
    for i in range(40):
        seq = hist + (["TAI", "XIU"] * 3)
        brain.learn(seq, "XIU" if i % 2 == 0 else "TAI")

    result = brain.think(["TAI", "TAI", "XIU", "TAI", "XIU", "XIU", "TAI"])
    assert "pred" in result
    print("OK think:", result)
    print("Stats:", brain.stats())


if __name__ == "__main__":
    test_brain_learn_and_predict()
    print("test_brain passed")
