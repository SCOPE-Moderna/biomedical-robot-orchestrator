from __future__ import annotations
import logging

from backend.db.conn import conn

logger = logging.getLogger(__name__)

EXPECTED_TABLE_NAMES = ["flow_runs", "instruments", "node_runs", "plate_locations"]


def create_tables_if_missing() -> None:
    logger.info("Checking for missing tables")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        )
        tables = cur.fetchall()
        tables = [table[0] for table in tables]

        if "flow_runs" not in tables:
            logger.info("Creating missing table flow_runs")
            cur.execute(
                """
            CREATE TABLE flow_runs
            (
                id                 SERIAL PRIMARY KEY,
                name               TEXT       NOT NULL,
                start_flow_node_id TEXT       NOT NULL,
                current_node_id    TEXT       NOT NULL,
                started_at         TIMESTAMP           DEFAULT NOW(),
                status             run_status NOT NULL DEFAULT 'in-progress'
            )
            """
            )
        else:
            logger.debug("Table flow_runs already exists")

        if "node_runs" not in tables:
            logger.info("Creating missing table node_runs")
            cur.execute(
                """
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
            """
            )
        else:
            logger.debug("Table node_runs already exists")

        if "instruments" not in tables:
            logger.info("Creating missing table instruments")
            cur.execute(
                """
            CREATE TABLE instruments
            (
                id                SERIAL PRIMARY KEY,
                name              TEXT NOT NULL,
                type              TEXT NOT NULL,
                connection_method TEXT NOT NULL,
                connection_info   JSONB,
                in_use_by         INTEGER REFERENCES node_runs (id),
                created_at        TIMESTAMP DEFAULT NOW(),
                updated_at        TIMESTAMP DEFAULT NOW()
            )
            """
            )
        else:
            logger.debug("Table instruments already exists")

        if "plate_locations" not in tables:
            logger.info("Creating missing table plate_locations")
            cur.execute(
                """
            CREATE TABLE plate_locations
            (
                id            TEXT UNIQUE PRIMARY KEY,
                type          TEXT, -- e.g. instrument, hotel, plate_holder, etc.
                in_use_by     INTEGER REFERENCES node_runs (id),
                instrument_id INTEGER REFERENCES instruments (id),
                parent_id     TEXT REFERENCES plate_locations (id),
                x_capacity    NUMERIC,
                y_capacity    NUMERIC
            )
            """
            )
        else:
            logger.debug("Table plate_locations already exists")
