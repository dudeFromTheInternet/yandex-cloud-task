import json
import uuid
import ydb
import ydb.iam

BACKEND_VERSION = "1.0.0"

class YDBDriver:
    def __init__(self):
        driver_config = ydb.DriverConfig(
            endpoint='grpcs://ydb.serverless.yandexcloud.net:2135',
            database='/ru-central1/b1gb847pco9bidh299j9/etn67d7cn7mhchffkla0',
            credentials=ydb.iam.MetadataUrlCredentials(),
            root_certificates=ydb.load_ydb_root_certificate(),
        )
        self.driver = ydb.Driver(driver_config)
        try:
            self.driver.wait(fail_fast=True, timeout=5)
        except TimeoutError:
            raise RuntimeError("Failed to connect to YDB")

    def create_session(self):
        return self.driver.table_client.session().create()

ydb_driver = YDBDriver()
TABLE_PATH = 'messages'

def initialize_ydb_table():
    session = ydb_driver.create_session()
    session.execute_scheme(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_PATH} (
            id Utf8,
            text Utf8,
            PRIMARY KEY (id)
        );
    """)

initialize_ydb_table()

def get_cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    }

def handler(event, context):
    query_params = event.get("queryStringParameters", {}) or {}
    method = event.get("httpMethod", "GET")

    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": get_cors_headers()
        }

    action = query_params.get("action", "")
    cors_headers = get_cors_headers()

    try:
        if action == "version" and method == "GET":
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"version": BACKEND_VERSION})
            }

        elif action == "get_messages" and method == "GET":
            session = ydb_driver.create_session()
            result_set = session.transaction().execute(
                f"SELECT id, text FROM {TABLE_PATH};", commit_tx=True
            )
            messages = [
                {"id": row["id"], "text": row["text"]}
                for row in result_set[0].rows
            ]
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(messages)
            }

        elif action == "post_message" and method == "POST":
            body = event.get("body", "")
            data = json.loads(body)
            text = data.get("text", "").strip()

            if not text:
                return {
                    "statusCode": 400,
                    "headers": cors_headers,
                    "body": json.dumps({"error": "Message text cannot be empty"})
                }

            message_id = str(uuid.uuid4())
            session = ydb_driver.create_session()
            session.transaction().execute(
                f"INSERT INTO {TABLE_PATH} (id, text) VALUES (\"{message_id}\", \"{text}\");",
                commit_tx=True
            )
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"id": message_id, "text": text})
            }

        elif action == "error" and method == "GET":
            return {
                "statusCode": 302,
                "headers": {
                    "Location": "https://guestbook-frontend.website.yandexcloud.net/",
                    **cors_headers
                },
                "body": ""
            }

        else:
            return {
                "statusCode": 404,
                "headers": cors_headers,
                "body": json.dumps({"error": "Invalid or missing action"})
            }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)})
        }
