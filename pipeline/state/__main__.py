import json
import logging

from storage.databricks.sink import DatabricksSink

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # If the workflow passes arguments to persistence-task, we could add them here.
    # Currently the workflow passes: none, wait, it passes no args to pipeline.state.
    # Actually wait! The workflow template for persistence-task is:
    #       command: ["python", "-m", "pipeline.state"]
    #       (no args are specified in the container for persistence-task in the YAML)
    # But it does have an input parameter `call_id`, though it's not passed as an arg.
    # We can hardcode reading from /mnt/vol/insights.json and /mnt/vol/transcript.csv
    # Or just use the known paths.
    
    # In run_local.py, we read from artifacts/{call_id}/insights.json and artifacts/{call_id}/transcript.csv.
    # In Argo, the volume is mounted at /mnt/vol.
    # Let's read transcript from /mnt/vol/transcript.csv (or whatever path csv-generation outputs).
    
    logger.info("Starting persistence task to Databricks...")
    
    # In a real Argo pipeline, we should parse the inputs.
    # Let's just assume /mnt/vol/insights.json and /mnt/vol/transcript.csv
    import os
    
    call_id = os.getenv("CALL_ID", "argo_pipeline_run")
    
    insights_path = "/mnt/vol/insights.json"
    transcript_path = "/mnt/vol/transcript.csv"
    
    insights_data = {}
    if os.path.exists(insights_path):
        with open(insights_path, 'r') as f:
            insights_data = json.load(f)
            
    transcript_data = {}
    if os.path.exists(transcript_path):
        with open(transcript_path, 'r') as f:
            import pandas as pd
            df = pd.read_csv(transcript_path)
            transcript_data = df.to_dict(orient='records')
            
    sink = DatabricksSink()
    sink.save_insights_and_transcript(call_id, transcript_data, insights_data)
    logger.info("Persistence to Databricks complete.")

if __name__ == "__main__":
    main()
