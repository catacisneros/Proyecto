# main.py
import os
from fastapi import FastAPI, Body
import uvicorn

from adk_app.workflows.credit_card_episode import run_episode_loop

app = FastAPI(title="FinLit Story Demo")

@app.post("/actions/run_credit_card_episode")
def run_credit_card_episode(body: dict = Body(...)):
    state = {
        "level": body.get("level", "beginner"),
        "persona": body.get("persona"),
        "user_goal": body.get("user_goal"),
        "monthly_budget": body.get("monthly_budget"),
        "current_balance": body.get("current_balance"),
        "days_until_due": body.get("days_until_due"),
        "apr_percent": body.get("apr_percent"),
        "utilization_percent": body.get("utilization_percent"),
    }
    result = run_episode_loop(state, max_iters=2)
    return {
        "episode": 1,
        "goal": "credit_card_basics",
        "shot_prompt": result.get("shot_prompt"),
        "video_uri": result.get("video_uri"),
        "choice_images": result.get("choice_images"),
        "choice_hints": result.get("choice_hints"),
        "critic": result.get("critic"),
        "rai": result.get("rai")
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)

    

