from __future__ import annotations

from datetime import datetime

from .conn import conn


class FlowRun:
    def __init__(
        self,
        id: int,
        start_node_id: str,
        current_node_id: str,
        started_at: datetime,
        status: str,
    ):
        self.id = id
        self.start_flow_node_id = start_node_id
        self.current_node_id = current_node_id
        self.started_at = started_at
        self.status = status

    @classmethod
    def fetch_from_id(cls, id: int) -> FlowRun:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, start_flow_node_id, current_node_id, started_at, flow_status FROM flow_runs WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()
            return cls(*row)

    @classmethod
    def create(cls, start_flow_node_id: str, status="running") -> FlowRun:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO flow_runs VALUES "
                "(flow_status = %s, start_flow_node_id = %s, current_node_id = %s)"
                "RETURNING id, started_at",
                (status, start_flow_node_id, start_flow_node_id),
            )
            [flow_run_id, started_at] = cur.fetchone()
            return cls(
                flow_run_id,
                start_flow_node_id,
                start_flow_node_id,
                started_at,
                status,
            )

    @staticmethod
    def query(
        run_id: int | None,
        status: str | None,
        start_node_id: str | None,
        current_node_id: str | None,
    ):
        query = "SELECT * FROM flow_runs WHERE 1 = 1"
        params = []

        if run_id is not None:
            query += " AND id = %s"
            params.append(run_id)
        if status is not None:
            query += " AND flow_status = %s"
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
            cur.execute(
                "UPDATE flow_runs SET current_node_id = %s, flow_status = %s WHERE id = %s",
                (current_node_id, self.id),
            )
        self.current_node_id = current_node_id
        self.status = new_status
