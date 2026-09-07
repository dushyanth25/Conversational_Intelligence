import json
import os

from databricks import sql
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DATABRICKS_HOST")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
token = os.getenv("DATABRICKS_TOKEN")
catalog = os.getenv("DATABRICKS_CATALOG", "workspace")
schema = os.getenv("DATABRICKS_SCHEMA", "default")
table = "conversations"

full_table_name = f"{catalog}.{schema}.{table}"

print(f"Connecting to Databricks to query '{full_table_name}'...")

try:
    with sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    ) as connection:

        with connection.cursor() as cursor:
            # Query the most recent 5 records
            query = f"SELECT call_id, created_at, insights FROM {full_table_name} ORDER BY created_at DESC LIMIT 5"
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                print("No data found in the table.")
            else:
                for row in rows:
                    call_id = row.call_id
                    created_at = row.created_at
                    insights = json.loads(row.insights) if row.insights else {}
                    
                    print(f"\n--- Call ID: {call_id} | Created: {created_at} ---")
                    print(f"Total Insights: {len(insights.get('insights', []))}")
                    for insight in insights.get("insights", [])[:2]: # preview first 2 insights
                        print(f" - {insight.get('parameter')}: {insight.get('result')}")
                    print(" ... (more insights omitted)")
                    
except Exception as e:
    print(f"Failed to query Databricks: {e}")
