import json

from config import get_settings

try:
    from databricks import sql
except ImportError:
    sql = None

class DatabricksSink:
    def __init__(self):
        self.settings = get_settings()
        
    def save_insights_and_transcript(self, call_id: str, transcript_data: dict, insights_data: dict):
        if not sql:
            print("Warning: databricks-sql-connector not installed. Cannot push to Databricks.")
            return

        host = self.settings.DATABRICKS_HOST
        http_path = self.settings.DATABRICKS_HTTP_PATH
        token = self.settings.DATABRICKS_TOKEN
        
        if not host or not http_path or not token:
            print("Databricks configuration missing. Skipping push to Databricks.")
            return
            
        print(f"DEBUG DATABRICKS: host='{host}', path='{http_path}', token_len={len(token.get_secret_value())}")

        try:
            connection = sql.connect(
                server_hostname=host,
                http_path=http_path,
                access_token=token.get_secret_value()
            )
            
            cursor = connection.cursor()
            
            # Ensure the table exists (this could also be done via Alembic or setup scripts, but for simplicity here)
            catalog = self.settings.DATABRICKS_CATALOG
            schema = self.settings.DATABRICKS_SCHEMA
            table = self.settings.DATABRICKS_TABLE
            full_table_name = f"{catalog}.{schema}.{table}"
            
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {full_table_name} (
                call_id STRING,
                transcript STRING,
                insights STRING,
                created_at TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            
            insert_query = f"""
            INSERT INTO {full_table_name} (call_id, transcript, insights, created_at)
            VALUES (?, ?, ?, current_timestamp())
            """
            
            cursor.execute(
                insert_query, 
                (
                    call_id, 
                    json.dumps(transcript_data), 
                    json.dumps(insights_data)
                )
            )
            
            cursor.close()
            connection.close()
            print(f"Successfully saved transcript and insights for call {call_id} to Databricks ({full_table_name})")
            
        except Exception as e:
            print(f"Error saving to Databricks: {e}")
