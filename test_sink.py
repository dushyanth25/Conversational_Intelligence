from storage.databricks.sink import DatabricksSink

sink = DatabricksSink()
try:
    sink.save_insights_and_transcript("test_call_id", {"test": "transcript"}, {"test": "insights"})
    print("SUCCESS_SINK")
except Exception as e:
    print(f"FAILED_SINK: {e}")
