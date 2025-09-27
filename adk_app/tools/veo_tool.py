# tools/veo_tool.py
# Minimal Veo wrapper for ADK agents. Uses REST + OAuth and polls LRO.

import os, time, base64, json
from typing import Optional, Dict, Any
import requests
import google.auth
from google.auth.transport.requests import Request

PROJECT_ID = os.getenv("GCP_PROJECT")
LOCATION = os.getenv("GCP_REGION", "us-central1")
MODEL_ID = os.getenv("VEO_MODEL_ID", "veo-3.0-fast-generate-001")  # fast for demos
OUTPUT_GCS = os.getenv("VEO_OUTPUT_GCS", "")  # e.g., gs://your-bucket/episodes/

VEO_ENDPOINT = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predictLongRunning"
)

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

def _wait_for_operation(op_name: str, token: str, poll=3, timeout=900) -> Dict[str, Any]:
    """Polls the LRO until done, returns the operation JSON when complete."""
    op_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/{op_name}"
    t0 = time.time()
    while True:
        r = requests.get(op_url, headers=_headers(token), timeout=60)
        r.raise_for_status()
        op = r.json()
        if op.get("done"):
            return op
        if time.time() - t0 > timeout:
            raise TimeoutError(f"Veo operation timed out: {op_name}")
        time.sleep(poll)

def generate_video(
    prompt: str,
    duration: int = 6,
    aspect_ratio: str = "16:9",
    resolution: Optional[str] = None,  # e.g., "1080p" for Veo 3
    sample_count: int = 1,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Text to video. Returns dict with {gcs_uris, base64_mp4s, rai_info}."""
    token = _get_bearer()

    params = {
        "aspectRatio": aspect_ratio,
        "sampleCount": sample_count,
    }
    if resolution:
        params["resolution"] = resolution
    if seed is not None:
        params["seed"] = seed

    instance = {"prompt": prompt}
    payload = {
        "instances": [instance],
        "parameters": params,
        "duration": duration,
    }
    if OUTPUT_GCS:
        payload["outputStorageUri"] = OUTPUT_GCS.rstrip("/") + "/"

    resp = requests.post(VEO_ENDPOINT, headers=_headers(token), data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    op_name = resp.json()["name"]

    op = _wait_for_operation(op_name, token)
    # When done, response contains videos either as GCS URIs or base64 bytes.
    result = op.get("response", {})
    media = result.get("predictions", [])
    out = {"gcs_uris": [], "base64_mp4s": [], "rai_info": {}}

    if "raiMediaFilteredCount" in result:
        out["rai_info"]["filtered_count"] = result["raiMediaFilteredCount"]
        out["rai_info"]["filtered_reasons"] = result.get("raiMediaFilteredReasons", [])

    for item in media:
        # Depending on output target, Veo returns GCS URIs or base64 bytes
        if "gcsUris" in item:
            out["gcs_uris"].extend(item["gcsUris"])
        elif "bytesBase64Encoded" in item:
            out["base64_mp4s"].append(item["bytesBase64Encoded"])
    return out
