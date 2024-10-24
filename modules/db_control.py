import psycopg


class SQLighter:
    def __init__(self, db_name: str, user: str, password: str, host: str, port: int):
        self.connection = psycopg.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        # self.connection.autocommit = True  # Enable autocommit to mimic SQLite's behavior
        self.cursor = self.connection.cursor(row_factory=psycopg.rows.dict_row)