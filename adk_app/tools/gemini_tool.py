# tools/gemini_tool.py
import os, json, requests, google.auth
from typing import Dict, Any
from google.auth.transport.requests import Request

PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-pro-002")

if not PROJECT_ID:
    raise EnvironmentError("Set GCP_PROJECT or GOOGLE_CLOUD_PROJECT for Gemini API calls")

ENDPOINT = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1/"
    f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:generateContent"
)

def _bearer() -> str:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    if not creds.valid:
        creds.refresh(Request())
    return creds.token

SYSTEM_RULES = (
    "You write a single cinematic shot prompt for a 6s educational clip about credit card use. "
    "Must be visually concrete and show numeric UI overlays that match user inputs. "
    "Keep under 70 words. Include terms: due date, interest, minimum payment, statement balance, utilization when relevant. "
    "Do not moralize. No sensitive PII. Output JSON with field 'shot_prompt'."
)

def generate_shot_prompt(fin_inputs: Dict[str, Any]) -> str:
    token = _bearer()
    content = [
        {"role": "user", "parts": [{"text": SYSTEM_RULES}]},
        {"role": "user", "parts": [{"text": json.dumps(fin_inputs)}]},
    ]
    body = {"contents": content, "generationConfig": {"temperature": 0.4}}
    r = requests.post(ENDPOINT, headers={"Authorization": f"Bearer {token}"}, json=body, timeout=60)
    r.raise_for_status()
    cand = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    # Model returns JSON text. Parse and return the shot_prompt.
    data = json.loads(cand)
    return data["shot_prompt"]
