from .evolution import SelfEvolution


class Brain:
    def __init__(self):
        self.evolution = SelfEvolution()

    def learn(self, history, actual):
        self.evolution.observe(history, actual)

    def think(self, history):
        result = self.evolution.predict(history)

        if result:
            return {
                "pred": result["prediction"],
                "score": 2.0 + float(result.get("accuracy", 0.5)) * 2.5,
                "reason": result.get("reason", f"Brain[{result.get('algorithm')}]"),
                "algorithm": result.get("algorithm"),
                "accuracy": result.get("accuracy"),
                "weight": result.get("weight"),
            }

        if not history:
            return {
                "pred": "TAI",
                "score": 1.0,
                "reason": "Brain: fallback empty",
                "algorithm": "fallback",
            }

        last = history[-1]
        recent = history[-8:] if len(history) >= 8 else history
        tai = recent.count("TAI")
        if tai >= 6:
            pred = "XIU"
        elif tai <= 2:
            pred = "TAI"
        else:
            pred = "XIU" if last == "TAI" else "TAI"

        return {
            "pred": pred,
            "score": 1.2,
            "reason": "Brain: fallback smart",
            "algorithm": "fallback",
        }

    def stats(self):
        return self.evolution.stats_summary()
