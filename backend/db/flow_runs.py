from __future__ import annotations

from datetime import datetime

from backend.node_connector_pb2.ui_pb2 import FlowRun as ProtoFlowRun
from backend.db.conn import conn


class FlowRun:
    def __init__(
        self,
        id: int,
        name: str,
        start_node_id: str,
        current_node_id: str,
        started_at: datetime,
        status: str,
    ):
        self.id = id
        self.name = name
        self.start_flow_node_id = start_node_id
        self.current_node_id = current_node_id
        self.started_at = started_at
        self.status = status

    @classmethod
    def fetch_from_id(cls, id: int) -> FlowRun:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, start_flow_node_id, current_node_id, started_at, status FROM flow_runs WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()
            return cls(*row)

    @classmethod
    def create(
        cls, name: str, start_flow_node_id: str, status="in-progress"
    ) -> FlowRun:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO flow_runs (name, status, start_flow_node_id, current_node_id) "
                "VALUES (%s, %s, %s, %s) "
                "RETURNING id, started_at",
                (name, status, start_flow_node_id, start_flow_node_id),
            )
            [flow_run_id, started_at] = cur.fetchone()
            return cls(
                flow_run_id,
                name,
                start_flow_node_id,
                start_flow_node_id,
                started_at,
                status,
            )

    @staticmethod
    def query(
        run_id: int | None = None,
        status: str | None = None,
        start_node_id: str | None = None,
        current_node_id: str | None = None,
        limit: int | None = None,
        order_by: str | None = None,
    ) -> list[FlowRun]:
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
        if order_by is not None:
            query += " ORDER BY %s"
            params.append(order_by)

        if limit is not None:
            query += " LIMIT %s"
            params.append(limit)
        else:
            query += " LIMIT 100"

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

            return [FlowRun(*row) for row in rows]

    def update_node(self, current_node_id: str, status: str | None) -> None:
        new_status = status if status is not None else self.status
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE flow_runs SET current_node_id = %s, status = %s WHERE id = %s",
                (current_node_id, status, self.id),
            )
        self.current_node_id = current_node_id
        self.status = new_status

    def to_proto(self) -> ProtoFlowRun:
        return ProtoFlowRun(
            id=self.id,
            name=self.name,
            start_flow_node_id=self.start_flow_node_id,
            current_node_id=self.current_node_id,
            started_at=self.started_at,
            status=self.status,
        )
