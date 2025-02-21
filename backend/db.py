from __future__ import annotations

import logging
from psycopg import connect

logger = logging.getLogger(__name__)

logger.info(f"Connecting to database")
conn = connect("postgres://vestradb_user:veggie_straws@127.0.0.1:5432/vestradb")
logger.info(f"Connected to database")

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

