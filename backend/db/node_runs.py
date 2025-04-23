from __future__ import annotations

import datetime
import json
from psycopg.types.json import Jsonb

from backend.db.conn import conn


class NodeRun:
    def __init__(
        self,
        _id: int,
        flow_run_id: int,
        node_id: str,
        input_data: dict,
        output_data: dict,
        started_at: datetime.datetime,
        finished_at: datetime.datetime,
        status: str,
    ):
        self.id = _id
        self.flow_run_id = flow_run_id
        self.node_id = node_id
        self.input_data = input_data
        self.output_data = output_data
        self.started_at = started_at
        self.finished_at = finished_at
        self.status = status

    @classmethod
    def fetch_from_id(cls, id: int) -> NodeRun:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM node_runs WHERE id = %s", (id,))
            row = cur.fetchone()
            return cls(*row)

    @classmethod
    def fetch_from_flowrun_and_node(cls, flow_run_id: int, node_id: str) -> NodeRun:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM node_runs WHERE flow_run_id = %s AND node_id = %s "
                # get newest if there are multiple
                "ORDER BY id DESC",
                (flow_run_id, node_id),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return cls(*row)

    @classmethod
    def create(cls, flow_run_id: int, node_id: str, input_data=None) -> NodeRun:
        if input_data is None:
            input_data = {}

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO node_runs (flow_run_id, node_id, input_data)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (flow_run_id, node_id, Jsonb(input_data)),
            )
            row = cur.fetchone()
            return cls(*row)

    def set_status(self, status: str) -> None:
        # if status is "completed", set finished_at to now
        if status == "completed":
            raise ValueError("Use complete() method to set status to completed")

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE node_runs SET status = %s, finished_at = %s WHERE id = %s",
                (status, self.finished_at, self.id),
            )

    def complete(self, output_data: dict | None = None) -> None:
        self.output_data = output_data
        self.status = "completed"
        self.finished_at = datetime.datetime.now()

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE node_runs SET status = %s, output_data = %s, finished_at = NOW() WHERE id = %s",
                ("completed", Jsonb(output_data), self.id),
            )
