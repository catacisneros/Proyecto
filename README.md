# FinLit ADK

FinLit ADK is a FastAPI microservice that assembles short, cinematic learning clips about responsible credit-card usage. It chains together Google ADK agents to plan a scenario, script a visual shot prompt with Gemini, render a Veo video clip, and produce branching guidance that helps learners decide the next action.

## Key Capabilities
- **Agentic workflow** – Sequential agents plan the story, write the prompt, generate media, and critique pedagogy using Google ADK primitives.
- **Generative integrations** – Uses Vertex AI Gemini for prompt authoring and Vertex AI Veo for text-to-video generation, with optional GCS delivery.
- **Choices & feedback** – Produces learner-facing branching images, hints, and rubric-aligned critique metadata.
- **Cloud-ready** – Ships with a lightweight Cloud Run Dockerfile and environment-driven configuration for easy deployment.

## Project Structure
```
finlit-adk/
├── adk_app/
│   ├── agents/              # Individual ADK agents (planner, prompt writer, video, critic, etc.)
│   ├── tools/               # Gemini & Veo API helpers
│   └── workflows/           # Episode orchestration logic
├── main.py                  # FastAPI entrypoint with episode endpoint
├── config.py                # .env loader and API key validation helper
├── requirements.txt         # Python dependencies
└── cloudrun.Dockerfile      # Container definition for Cloud Run
```

## Prerequisites
- Python 3.11+
- A Google Cloud project with Vertex AI enabled
- Service account or user credentials granting `Vertex AI User` and storage access (if writing to GCS)
- `gcloud` CLI configured with the target project (required for deployment/testing tools)

## Setup
1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   - Copy `.env` and adjust values for your project/region/models if needed.
   - Ensure application default credentials are available via `gcloud auth application-default login` or by setting `GOOGLE_APPLICATION_CREDENTIALS` to a service-account JSON file.

## Running Locally
1. Validate that required API keys and IDs are set:
   ```bash
   python -c "import config; config.validate_api_keys()"
   ```
2. Launch the API (choose one):
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8080
   # or
   python main.py
   ```
3. Test the endpoint:
   ```bash
   curl -X POST http://localhost:8080/actions/run_credit_card_episode \
     -H "Content-Type: application/json" \
     -d '{
           "level": "beginner",
           "persona": "recent graduate",
           "user_goal": "avoid interest and build credit",
           "monthly_budget": 800,
           "current_balance": 450,
           "days_until_due": 12,
           "apr_percent": 22.4,
           "utilization_percent": 35
         }'
   ```
   The response consolidates the generated shot prompt, video URI/base64, branching image metadata, hints, and a critic decision.

## Workflow Highlights
The episode workflow (`adk_app/workflows/credit_card_episode.py`) runs the following agents in sequence:
1. **StoryPlannerAgent** – Shapes the episode spec, objectives, and branch labels.
2. **PromptWriterAgent** – Calls `generate_shot_prompt` to craft a cinematic Gemini prompt tailored to learner inputs.
3. **VideoAgent** – Invokes `generate_video` to create a Veo clip (GCS URI or base64 payload).
4. **ChoiceImageAgent / ChoiceHintAgent** – Produce illustrative branch choices and guidance.
5. **PedagogyCriticAgent** – Scores keyword coverage; can request prompt revisions before accepting.

The loop retries once more if the critic flags missing rubric coverage.

## Environment Variables
| Variable | Description |
| --- | --- |
| `GCP_PROJECT` / `GOOGLE_CLOUD_PROJECT` | Target Google Cloud project ID (required). |
| `GCP_REGION` / `GOOGLE_CLOUD_REGION` | Vertex AI region (defaults to `us-central1`). |
| `GEMINI_MODEL_ID` | Gemini model resource name (e.g., `google/gemini-2.5-pro`). |
| `VEO_MODEL_ID` | Veo model resource (e.g., `veo-3.0-fast-generate-001`). |
| `VEO_OUTPUT_GCS` | Optional GCS prefix for rendered videos. |
| `PORT` | Port FastAPI listens on (defaults to `8080`). |
| `GOOGLE_APPLICATION_CREDENTIALS` | Optional path to service-account key file for local runs. |

## Deployment (Cloud Run)
1. **Authenticate** (if not already):
   ```bash
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project $GCP_PROJECT
   ```
2. **Build the container image**
   ```bash
   gcloud builds submit --tag gcr.io/$GCP_PROJECT/finlit-adk
   ```
3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy finlit-adk \
     --image gcr.io/$GCP_PROJECT/finlit-adk \
     --region $GCP_REGION \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars GCP_PROJECT=$GCP_PROJECT,GCP_REGION=$GCP_REGION,
                    GEMINI_MODEL_ID=$GEMINI_MODEL_ID,VEO_MODEL_ID=$VEO_MODEL_ID,
                    VEO_OUTPUT_GCS=$VEO_OUTPUT_GCS
   ```
4. **Invoke the service** using the Cloud Run HTTPS URL (same JSON payload as local testing).

## Troubleshooting & Notes
- Ensure Vertex AI quota permits Gemini and Veo requests in your region.
- For Veo outputs in GCS, the service account must have `roles/storage.objectAdmin` on the target bucket.
- Network calls rely on Google Application Default Credentials; rotate tokens periodically for long-lived deployments.

## License
Specify license terms here if required by your organization or competition guidelines.
