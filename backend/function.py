import json
import uuid
import ydb
import ydb.iam

BACKEND_VERSION = "1.0.0"

def create_ydb_driver():
    driver_config = ydb.DriverConfig(
        endpoint="ydb.serverless.yandexcloud.net:2135",
        database="/ru-central1/b1gb847pco9bidh299j9/etn67d7cn7mhchffkla0",
        credentials=ydb.iam.MetadataUrlCredentials(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )
    driver = ydb.Driver(driver_config)
    try:
        driver.wait(fail_fast=True, timeout=5)
    except TimeoutError:
        raise RuntimeError("Connect failed to YDB")
    return driver

def initialize_ydb_table(driver, table_path):
    session = driver.table_client.session().create()
    session.execute_scheme(f"""
        CREATE TABLE IF NOT EXISTS {table_path} (
            id Utf8,
            text Utf8,
            PRIMARY KEY (id)
        );
    """)

ydb_driver = create_ydb_driver()
TABLE_PATH = 'guestbook'
initialize_ydb_table(ydb_driver, TABLE_PATH)

def handler(event):
    query_params = event.get("queryStringParameters", {}) or {}
    method = event.get("httpMethod", "GET")

    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": cors_headers
        }

    action = query_params.get("action", "")

    if action == "version" and method == "GET":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({"version": BACKEND_VERSION})
        }

    elif action == "get_messages" and method == "GET":
        try:
            session = ydb_driver.table_client.session().create()
            result_set = session.transaction().execute(f"SELECT id, text FROM {TABLE_PATH};", commit_tx=True)
            messages = [{"id": row["id"], "text": row["text"]} for row in result_set[0].rows]
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(messages)
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps({"error": str(e)})
            }

    elif action == "post_message" and method == "POST":
        body = event.get("body", "")
        try:
            data = json.loads(body)
            text = data.get("text", "").strip()
            if not text:
                return {
                    "statusCode": 400,
                    "headers": cors_headers,
                    "body": json.dumps({"error": "Message text cannot be empty"})
                }

            message_id = str(uuid.uuid4())
            session = ydb_driver.table_client.session().create()
            session.transaction().execute(f"""
                INSERT INTO {TABLE_PATH} (id, text) VALUES ("{message_id}", "{text}");
            """, commit_tx=True)

            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"id": message_id, "text": text})
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps({"error": str(e)})
            }

    elif action == "error" and method == "GET":
        return {
            "statusCode": 302,
            "headers": {"Location": "", **cors_headers},
            "body": ""
        }

    else:
        return {
            "statusCode": 404,
            "headers": cors_headers,
            "body": json.dumps({"error": "Invalid or missing action"})
        }