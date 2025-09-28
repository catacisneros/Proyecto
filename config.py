from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "google/gemini-2.5-pro")
VEO_MODEL_ID = os.getenv("VEO_MODEL_ID", "veo-3.0-fast-generate-001")
VEO_OUTPUT_GCS = os.getenv("VEO_OUTPUT_GCS")


@dataclass(frozen=True)
class Settings:
    project: str | None = GCP_PROJECT
    region: str = GCP_REGION
    gemini_model_id: str = GEMINI_MODEL_ID
    veo_model_id: str = VEO_MODEL_ID
    veo_output_gcs: str | None = VEO_OUTPUT_GCS


SETTINGS = Settings()


def require_project() -> str:
    """Ensure a GCP project is configured before making API calls."""
    if not SETTINGS.project:
        raise EnvironmentError("Set GCP_PROJECT or GOOGLE_CLOUD_PROJECT before using Vertex AI or GCS clients")
    return SETTINGS.project
