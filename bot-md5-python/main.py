import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import PORT, FETCH_INTERVAL, WARMUP_ROUNDS, AUTO_GIT_PUSH
from core.fetch import fetch_data
from core.state import load_state, save_state
from core.ensemble import ensemble_predict, record_feedback, brain
from brain.github_sync import GitHubSync

state = load_state()
history = state.get("history", [])
stats = state.get("stats", {"total": 0, "correct": 0, "wrong": 0})
last_session = state.get("last_session")
git_sync = GitHubSync()
_algo_version_seen = 0


async def background_loop():
    global history, stats, last_session, _algo_version_seen

    while True:
        try:
            data = await fetch_data()
            if not data:
                await asyncio.sleep(FETCH_INTERVAL)
                continue

            data.sort(key=lambda x: x.get("GameSessionID", 0))
            new_items = [
                x for x in data if x.get("GameSessionID", 0) > (last_session or 0)
            ]

            for item in new_items:
                sid = item["GameSessionID"]
                d1 = int(item["Dice1"])
                d2 = int(item["Dice2"])
                d3 = int(item["Dice3"])
                total = d1 + d2 + d3
                outcome = "TAI" if total > 10 else "XIU"

                pred_result = ensemble_predict(history)

                if history and history[-1].get("pred"):
                    prev_reason = (history[-1].get("reason") or "").lower()
                    if "warmup" not in prev_reason and "fallback" not in prev_reason:
                        stats["total"] += 1
                        prev_pred = history[-1]["pred"]
                        if prev_pred == outcome:
                            stats["correct"] += 1
                        else:
                            stats["wrong"] += 1
                        record_feedback(history, outcome)

                history.append({
                    "sessionId": sid,
                    "dice": [d1, d2, d3],
                    "sum": total,
                    "outcome": outcome,
                    "pred": pred_result.get("pred"),
                    "confidence": pred_result.get("confidence", 0),
                    "reason": pred_result.get("reason", ""),
                    "receivedAt": datetime.now(timezone.utc).isoformat(),
                })

                if len(history) > 2000:
                    history = history[-1800:]

                last_session = sid
                print(f"Van {sid}: {d1}-{d2}-{d3} = {total} ({outcome})")
                if pred_result.get("pred"):
                    print(
                        f"Du doan: {pred_result['pred']} "
                        f"({pred_result.get('confidence')}%) | {pred_result.get('reason')}"
                    )

            if new_items:
                save_state({
                    "history": history,
                    "stats": stats,
                    "last_session": last_session,
                })

                if stats.get("total", 0) >= 60 and stats["total"] % 60 == 0:
                    try:
                        from brain.self_code_evolution_deep import DeepSelfCodeEvolution
                        from core.ensemble import get_module_stats

                        evo = DeepSelfCodeEvolution()
                        result = evo.run_once(history, get_module_stats())
                        print("[DEEP-EVO]", result.get("status"))
                    except Exception as e:
                        print("[DEEP-EVO] error:", e)

                bstats = brain.stats()
                ver = bstats.get("version", 0)
                if AUTO_GIT_PUSH and ver > _algo_version_seen and bstats.get("active", 0) > 0:
                    msg = f"brain: v{ver} active={bstats.get('active')} patterns={bstats.get('patterns_learned')}"
                    result = git_sync.sync(msg)
                    print(f"Git sync: {result}")
                    _algo_version_seen = ver

        except Exception as e:
            print("Loop error:", e)

        await asyncio.sleep(FETCH_INTERVAL)


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(background_loop())
    yield
    task.cancel()


app = FastAPI(title="Bot MD5 Python - Brain Evolution", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "running",
        "history": len(history),
        "stats": stats,
        "brain": brain.stats(),
    }


@app.get("/api/bot/status")
def status():
    pred = ensemble_predict(history)
    return {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "stats": stats,
        "prediction": pred,
        "brain": brain.stats(),
        "canPredict": len(history) >= WARMUP_ROUNDS,
    }


@app.get("/api/bot/brain")
def brain_info():
    return brain.stats()


@app.post("/api/bot/evolve")
def force_evolve():
    from brain.self_code_evolution_deep import DeepSelfCodeEvolution
    from core.ensemble import get_module_stats
    return DeepSelfCodeEvolution().run_once(history, get_module_stats())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
