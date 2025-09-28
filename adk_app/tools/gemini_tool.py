# tools/gemini_tool.py
import os, json, re, requests, google.auth
from typing import Dict, Any
from google.auth.transport.requests import Request

PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
MODEL_ID = os.getenv("GEMINI_MODEL_ID", "google/gemini-2.5-pro")

if not PROJECT_ID:
    raise EnvironmentError("Set GCP_PROJECT or GOOGLE_CLOUD_PROJECT for Gemini API calls")

_API_ROOT = f"https://{LOCATION}-aiplatform.googleapis.com/v1beta1"
_PROJECT_PREFIX = f"projects/{PROJECT_ID}/locations/{LOCATION}"


def _model_resource(model_id: str) -> str:
    """Return fully-qualified Gemini resource path supporting version names."""
    if model_id.startswith("projects/"):
        return model_id
    if model_id.startswith("publishers/") or model_id.startswith("models/"):
        return f"{_PROJECT_PREFIX}/{model_id}"
    if "/" in model_id:
        publisher, name = model_id.split("/", 1)
        return f"{_PROJECT_PREFIX}/publishers/{publisher}/models/{name}"
    return f"{_PROJECT_PREFIX}/publishers/google/models/{model_id}"


def _endpoint() -> str:
    return f"{_API_ROOT}/{_model_resource(MODEL_ID)}:generateContent"

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
    r = requests.post(_endpoint(), headers={"Authorization": f"Bearer {token}"}, json=body, timeout=60)
    r.raise_for_status()
    cand = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _extract_shot_prompt(cand)


def _extract_shot_prompt(raw_text: str) -> str:
    """Parse Gemini response allowing for code fences or loose JSON."""
    text = raw_text.strip()

    if text.startswith("```"):
        fences = text.split("```")
        if len(fences) >= 3:
            text = fences[1].split("\n", 1)[-1].strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict) and "shot_prompt" in data:
            return data["shot_prompt"]
    except json.JSONDecodeError:
        pass

    match = re.search(r'"shot_prompt"\s*:\s*"(?P<val>.+?)"\s*(,|}|$)', text, flags=re.DOTALL)
    if match:
        snippet = match.group("val")
        try:
            return json.loads(f'"{snippet}"')
        except json.JSONDecodeError:
            return snippet

    return text
