from __future__ import annotations

import logging
from psycopg import connect

logger = logging.getLogger(__name__)

logger.info(f"Connecting to database")
conn = connect("postgres://vestradb_user:veggie_straws@127.0.0.1:5432/vestradb")
logger.info(f"Connected to database")

EXPECTED_TABLE_NAMES = ["flow_runs", "instruments", "node_runs", "plate_locations"]

def create_tables_if_missing() -> None:
    logger.info("Checking for missing tables")
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()

        if "flow_runs" not in tables:
            logger.info("Creating missing table flow_runs")
            cur.execute("""
            CREATE TABLE flow_runs
            (
                id                 SERIAL PRIMARY KEY,
                name               TEXT       NOT NULL,
                start_flow_node_id TEXT       NOT NULL,
                current_node_id    TEXT       NOT NULL,
                started_at         TIMESTAMP           DEFAULT NOW(),
                status             run_status NOT NULL DEFAULT 'in-progress'
            )
            """)
        else:
            logger.debug("Table flow_runs already exists")

        if "node_runs" not in tables:
            logger.info("Creating missing table node_runs")
            cur.execute("""
            CREATE TABLE node_runs
            (
                id          SERIAL PRIMARY KEY,
                flow_run_id INTEGER    NOT NULL REFERENCES flow_runs (id),
                node_id     TEXT       NOT NULL,
                input_data  JSONB,
                output_data JSONB,
                started_at  TIMESTAMP           DEFAULT NOW(),
                finished_at TIMESTAMP,
                status      run_status NOT NULL DEFAULT 'in-progress'
            )
            """)
        else:
            logger.debug("Table node_runs already exists")

        if "instruments" not in tables:
            logger.info("Creating missing table instruments")
            cur.execute("""
            CREATE TABLE instruments
            (
                id                SERIAL PRIMARY KEY,
                name              TEXT NOT NULL,
                type              TEXT NOT NULL,
                connection_method TEXT NOT NULL,
                connection_info   JSONB,
                in_use_by         INTEGER REFERENCES node_runs (id),
                created_at        TEXT NOT NULL,
                updated_at        TIMESTAMP DEFAULT NOW()
            )
            """)
        else:
            logger.debug("Table instruments already exists")

        if "plate_locations" not in tables:
            logger.info("Creating missing table plate_locations")
            cur.execute("""
            CREATE TABLE plate_locations
            (
                id            TEXT UNIQUE PRIMARY KEY,
                type          TEXT, -- e.g. instrument, hotel, plate_holder, etc.
                in_use_by     INTEGER REFERENCES node_runs (id),
                instrument_id INTEGER REFERENCES instruments (id),
                parent_id     TEXT REFERENCES plate_locations (id),
                x_capacity    NUMERIC,
                y_capacity    NUMERIC
            );
            """)
        else:
            logger.debug("Table plate_locations already exists")

create_tables_if_missing()

class FlowRun:
    def __init__(self, id: int, status: str, start_node_id: str, current_node_id: str):
        self.id = id
        self.status = status
        self.start_node_id = start_node_id
        self.current_node_id = current_node_id

    @classmethod
    def fetch_from_id(cls, id: int) -> FlowRun:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM flow_runs WHERE id = %s", (id,))
            row = cur.fetchone()
            return cls(*row)

    @classmethod
    def new_from_start_node_id(cls, start_node_id: str, status = "running") -> FlowRun:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO flow_runs VALUES "
                        "(status = %s, start_node_id = %s, current_node_id = %s)"
                        "RETURNING id",
                        (status, start_node_id, start_node_id))
            row = cur.fetchone()
            return cls(row[0], status, start_node_id, start_node_id)

    @staticmethod
    def query(run_id: int | None, status: str | None, start_node_id: str | None, current_node_id: str | None):
        query = "SELECT * FROM flow_runs WHERE 1 = 1"
        params = []

        if run_id is not None:
            query += " AND id = %s"
            params.append(run_id)
        if status is not None:
            query += " AND status = %s"
            params.append(status)
        if start_node_id is not None:
            query += " AND start_node_id = %s"
            params.append(start_node_id)
        if current_node_id is not None:
            query += " AND current_node_id = %s"
            params.append(current_node_id)

        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def update_node(self, current_node_id: str, status: str | None) -> None:
        new_status = status if status is not None else self.status
        with conn.cursor() as cur:
            cur.execute("UPDATE flow_runs SET current_node_id = %s, status = %s WHERE id = %s",
                        (current_node_id, self.id))
        self.current_node_id = current_node_id
        self.status = new_status

