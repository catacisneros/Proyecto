"""FastAPI entrypoint for FinLit ADK."""

from datetime import datetime, timezone
import os
from typing import Tuple

from fastapi import Body, FastAPI, HTTPException
from google.auth import default
from google.cloud import storage
import uvicorn

from adk_app.workflows.credit_card_episode import run_episode_loop
from config import SETTINGS, require_project

app = FastAPI(title="FinLit Story Demo")


def _parse_gcs_uri(uri: str) -> Tuple[str, str]:
    if not uri.startswith("gs://"):
        raise ValueError("VEO_OUTPUT_GCS must be a valid gs:// URI")
    without_scheme = uri[5:]
    parts = without_scheme.split("/", 1)
    bucket = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    return bucket, prefix.rstrip("/")


@app.get("/")
def health_check():
    return {"status": "healthy", "message": "FinLit ADK is running"}


@app.get("/healthz")
def readiness_probe():
    return {"status": "ok"}


@app.post("/episodes/test")
def run_storage_smoke():
    project = require_project()
    if not SETTINGS.veo_output_gcs:
        raise HTTPException(status_code=400, detail="Set VEO_OUTPUT_GCS to use the smoke test endpoint")

    bucket_name, prefix = _parse_gcs_uri(SETTINGS.veo_output_gcs)
    creds, _ = default()
    client = storage.Client(project=project, credentials=creds)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    object_name = f"{prefix + '/' if prefix else ''}smoke-test-{timestamp}.txt"
    blob = client.bucket(bucket_name).blob(object_name)
    blob.upload_from_string("FinLit ADK smoke test", content_type="text/plain")

    return {"uri": f"gs://{bucket_name}/{object_name}"}


@app.post("/actions/run_credit_card_episode")
def run_credit_card_episode(body: dict = Body(...)):
    try:
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
            "rai": result.get("rai"),
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

    
