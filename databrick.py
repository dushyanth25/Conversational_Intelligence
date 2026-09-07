import os

from databricks import sql

hostname = os.getenv("DATABRICKS_SERVER_HOSTNAME")
http_path = os.getenv("DATABRICKS_HTTP_PATH")
token = os.getenv("DATABRICKS_TOKEN")

print("Server hostname:", hostname)
print("HTTP path:", http_path)
print("Token present:", bool(token))

try:
    with sql.connect(
        server_hostname=hostname,
        http_path=http_path,
        access_token=token,
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute("SHOW CATALOGS")
            catalogs = cursor.fetchall()
            print("CATALOGS:", catalogs)
            
            for catalog in catalogs:
                cat_name = catalog[0]
                try:
                    cursor.execute(f"SHOW SCHEMAS IN {cat_name}")
                    schemas = cursor.fetchall()
                    print(f"SCHEMAS IN {cat_name}:", schemas)
                except Exception as e:
                    print(f"Could not list schemas in {cat_name}: {e}")

            print("SUCCESS")

except Exception as e:
    print("FAILED")
    print(type(e).__name__, ":", e)