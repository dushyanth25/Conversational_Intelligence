# Conversational Intelligence Processing Pipeline

This is an open-source, robust, and scalable backend pipeline that processes conversational audio to extract deep business insights using LLMs (powered by Groq).

## Architecture

The pipeline orchestrates machine learning models and API calls to process audio asynchronously using **Argo Workflows** on Kubernetes.

1. **API (FastAPI)**: Lightweight gateway that accepts processing requests.
2. **Preprocessing**: Normalizes audio for consistent model inputs.
3. **VAD (Silero)**: Detects voice activity boundaries.
4. **ASR (faster-whisper)**: Generates timestamped transcriptions.
5. **Diarization (pyannote.audio)**: Assigns speaker labels to timestamps.
6. **Alignment & Tagging**: Merges ASR and diarization to create a canonical transcript.
7. **Insight Batching**: Parses dynamic prompt CSVs and chunks requests.
8. **Groq Insight Processing**: Fans out LLM requests in parallel to extract structured insights.
9. **Aggregation**: Collects and validates all partial LLM outputs into a final deterministic result.
10. **Storage**: Saves artifacts to **MinIO** and structured metadata to **PostgreSQL**.

## Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional for local testing)
- Kubernetes Cluster (local via minikube/kind or cloud)
- Argo Workflows installed on Kubernetes
- MinIO instance
- PostgreSQL (14+) instance
- Groq API Key (`GROQ_API_KEY`)
- HuggingFace Token (for pyannote diarization)

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API Key for LLM Inference |
| `HF_AUTH_TOKEN` | Hugging Face token for pyannote |
| `DATABASE_URL` | PostgreSQL connection string |
| `MINIO_ENDPOINT` | MinIO host |
| `MINIO_ACCESS_KEY` | MinIO Access Key |
| `MINIO_SECRET_KEY` | MinIO Secret Key |
| `ARGO_SERVER` | Argo Workflow Controller endpoint |
| `ARGO_NAMESPACE` | Kubernetes namespace for workflow |

## Local Development & Docker

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

2. Setup Database Migrations:
```bash
alembic upgrade head
```

3. Docker Build:
```bash
docker build -t conversation-intelligence-worker:latest .
```

## Kubernetes & Argo Setup

Deploy the workflow controller limits and workflow template:

```bash
kubectl apply -f deploy/kubernetes/workflow-controller.yaml
kubectl apply -f workflows/argo/conversation-intelligence-workflow.yaml
```

*Note: ASR and Diarization steps require nodes with GPUs. Ensure you have `nvidia.com/gpu` taints/tolerations or adjust `gpu_count=0` for CPU execution.*

## API Usage

Start the API:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Submit Processing Job

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "s3://conversation-intelligence/raw/call_001.wav",
    "prompt_sheet": "s3://conversation-intelligence/prompts/insights.csv",
    "call_id": "CALL_001",
    "parallel_workers": 5
  }'
```

**Response**:
```json
{
  "workflow_id": "conversation-pipeline-abc12",
  "call_id": "CALL_001",
  "status": "SUBMITTED"
}
```

## Input/Output Formats

**Prompt CSV Format**:
The prompt sheet should be a CSV with `parameter` and `prompt` columns.

**Final JSON Output**:
Located in MinIO: `insights/CALL_001.json`
```json
{
  "call_id": "CALL_001",
  "insights": [
    {
      "parameter": "sentiment",
      "result": "negative",
      "confidence": 0.95,
      "evidence": [
        {"timestamp": "00:03:21", "speaker": "CUSTOMER", "text": "I am unhappy with this."}
      ]
    }
  ]
}
```

## Troubleshooting & Concurrency

- **Retries**: Configured natively inside the Argo Workflow YAML. Groq HTTP 429s trigger exponential backoffs via the Python LLM client.
- **Workflow Cleanup**: Workflows have configured TTLs in Argo (`ttlStrategy`), retaining success for 1 hour and failures for 24 hours. Artifacts in MinIO/PostgreSQL persist indefinitely.
- **Concurrency**: Adjust `parallel_workers` in the API payload to control batch parallelism per call. Adjust `parallelism` in the Argo ConfigMap to limit the total concurrent workflows.
