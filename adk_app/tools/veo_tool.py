# tools/veo_tool.py
# Minimal Veo wrapper for ADK agents. Uses REST + OAuth and supports LRO polling.

import os
import time
import json
from typing import Optional, Dict, Any
import requests
import google.auth
from google.auth.transport.requests import Request

PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
MODEL_ID = os.getenv("VEO_MODEL_ID", "veo-3.0-fast-generate-001")  # fast for demos
OUTPUT_GCS = os.getenv("VEO_OUTPUT_GCS", "")  # e.g., gs://your-bucket/episodes/

if not PROJECT_ID:
    raise EnvironmentError("Set GCP_PROJECT or GOOGLE_CLOUD_PROJECT for Veo API calls")

_API_ROOT = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1"
_PROJECT_PREFIX = f"projects/{PROJECT_ID}/locations/{LOCATION}"


def _model_resource(model_id: str) -> str:
    if model_id.startswith("projects/"):
        return model_id
    if model_id.startswith("publishers/") or model_id.startswith("models/"):
        return f"{_PROJECT_PREFIX}/{model_id}"
    if "/" in model_id:
        publisher, name = model_id.split("/", 1)
        return f"{_PROJECT_PREFIX}/publishers/{publisher}/models/{name}"
    return f"{_PROJECT_PREFIX}/publishers/google/models/{model_id}"


def _veo_endpoint() -> str:
    return f"{_API_ROOT}/{_model_resource(MODEL_ID)}:generateContent"


def _get_bearer() -> str:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def _wait_for_operation(op_name: str, token: str, poll: int = 3, timeout: int = 900) -> Dict[str, Any]:
    """Poll the long-running operation until completion."""
    op_url = f"{_API_ROOT}/{op_name}"
    t0 = time.time()
    while True:
        response = requests.get(op_url, headers=_headers(token), timeout=60)
        response.raise_for_status()
        op = response.json()
        if op.get("done"):
            return op
        if time.time() - t0 > timeout:
            raise TimeoutError(f"Veo operation timed out: {op_name}")
        time.sleep(poll)


def _extract_media(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Veo media payload into URIs/Base64 plus safety metadata."""
    out = {"gcs_uris": [], "base64_mp4s": [], "rai_info": {}}

    candidates = result.get("candidates", [])
    for cand in candidates:
        content = cand.get("content", {})
        for part in content.get("parts", []):
            file_data = part.get("fileData")
            if not file_data:
                continue
            uri = file_data.get("fileUri")
            if uri:
                out["gcs_uris"].append(uri)
            data = file_data.get("data")
            if data:
                out["base64_mp4s"].append(data)
        # Capture any safety metadata if present.
        safety = cand.get("safetyRatings") or cand.get("safetyMetadata")
        if safety:
            out["rai_info"].setdefault("safety", safety)

    usage = result.get("usageMetadata")
    if usage:
        out["rai_info"]["usage"] = usage

    filtered = result.get("raiMediaFilteredCount")
    if filtered is not None:
        out["rai_info"]["filtered_count"] = filtered
        out["rai_info"]["filtered_reasons"] = result.get("raiMediaFilteredReasons", [])

    return out


def generate_video(
    prompt: str,
    duration: int = 6,
    aspect_ratio: str = "16:9",
    resolution: Optional[str] = None,
    sample_count: int = 1,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Request video generation via Veo generateContent REST API."""
    token = _get_bearer()

    generation_config: Dict[str, Any] = {
        "durationSeconds": duration,
        "aspectRatio": aspect_ratio,
        "numberOfVideos": sample_count,
    }
    if resolution:
        generation_config["resolution"] = resolution
    if seed is not None:
        generation_config["seed"] = seed

    request_body: Dict[str, Any] = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": generation_config,
    }

    if OUTPUT_GCS:
        request_body["output"] = {
            "storageConfig": {"gcsPath": OUTPUT_GCS.rstrip("/") + "/"}
        }

    response = requests.post(_veo_endpoint(), headers=_headers(token), json=request_body, timeout=60)
    response.raise_for_status()
    result = response.json()

    # Veo may return a long-running operation; poll until finished if needed.
    if "candidates" not in result and "response" not in result and "done" not in result and "name" in result:
        op = _wait_for_operation(result["name"], token)
        result = op.get("response", result)
    elif result.get("done") and "response" in result:
        result = result["response"]

    return _extract_media(result)
