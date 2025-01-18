import ydb
import ydb.iam

# Constants
YDB_ENDPOINT = 'grpcs://ydb.serverless.yandexcloud.net:2135'
YDB_DATABASE = '/ru-central1/b1g1i1fb1m9d7e4pd2ne/etn13nl9gtts5e5fel1k'
SA_KEY_FILE = 'key.json'
TABLE_PATH = 'messages'


def create_ydb_driver(endpoint: str, database: str, credentials_file: str) -> ydb.Driver:
    try:
        driver_config = ydb.DriverConfig(
            endpoint=endpoint,
            database=database,
            credentials=ydb.iam.ServiceAccountCredentials.from_file(credentials_file),
        )
        driver = ydb.Driver(driver_config)
        driver.wait(fail_fast=True, timeout=5)
        return driver
    except TimeoutError as e:
        raise RuntimeError("Failed to connect to YDB: Timeout.") from e
    except Exception as e:
        raise RuntimeError(f"Failed to connect to YDB: {e}") from e


def initialize_ydb_table(driver: ydb.Driver, table_path: str) -> None:
    try:
        with driver.table_client.session().create() as session:
            session.execute_scheme(f"""
                CREATE TABLE IF NOT EXISTS {table_path} (
                    id Utf8,
                    text Utf8,
                    PRIMARY KEY (id)
                );
            """)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize table '{table_path}': {e}") from e


def main():

    print("Initializing YDB driver and creating schema...")
    try:
        ydb_driver = create_ydb_driver(YDB_ENDPOINT, YDB_DATABASE, SA_KEY_FILE)
        initialize_ydb_table(ydb_driver, TABLE_PATH)
        print(f"Table '{TABLE_PATH}' initialized successfully.")
    except RuntimeError as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
