from __future__ import annotations

from backend.db.node_runs import NodeRun
from backend.db.conn import conn

import uuid


class PlateLocation:
    def __init__(
        self,
        id: str,
        type: str | None,
        in_use_by: int | None,
        instrument_id: int | None,
        parent_id: str | None,
        x_capacity: int | None,
        y_capacity: int | None,
    ):
        self.id = id
        self.type = type
        self.in_use_by = in_use_by
        self.instrument_id = instrument_id
        self.parent_id = parent_id
        self.x_capacity = x_capacity
        self.y_capacity = y_capacity

    @classmethod
    def fetch_from_ids(cls, ids: list[str]) -> list[PlateLocation]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM plate_locations WHERE id = ANY(%s)",
                (ids,),
            )
            rows = cur.fetchall()
            return [cls(*row) for row in rows]

    @classmethod
    def fetch_from_instrument_id(cls, instrument_id: int) -> list[PlateLocation]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM plate_locations WHERE instrument_id = %s",
                (instrument_id,),
            )
            rows = cur.fetchall()
            return [cls(*row) for row in rows]

    @classmethod
    def create(
        cls, instrument_id: int, x_capacity: int = 1, y_capacity: int = 1
    ) -> PlateLocation:
        with conn.cursor() as cur:
            new_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO plate_locations (id, instrument_id, x_capacity, y_capacity) "
                "VALUES (%s, %s, %s, %s) "
                "RETURNING id, type, in_use_by, instrument_id, parent_id, x_capacity, y_capacity",
                (new_id, instrument_id, x_capacity, y_capacity),
            )
            [id, type, in_use_by, instrument_id, parent_id, x_capacity, y_capacity] = (
                cur.fetchone()
            )
            return cls(
                id,
                type,
                in_use_by,
                instrument_id,
                parent_id,
                x_capacity,
                y_capacity,
            )

    def set_in_use_by(self, node_run_id: int | None, node_run: NodeRun | None = None):
        if node_run is not None:
            node_run_id = node_run.id

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE plate_locations SET in_use_by = %s WHERE id = %s",
                (node_run_id, self.id),
            )

    @staticmethod
    def set_in_use_by_many(
        plate_locations: list[PlateLocation], node_run_id: int | None, node_run: NodeRun
    ):
        if node_run is not None:
            node_run_id = node_run.id

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE plate_locations SET in_use_by = %s WHERE id = ANY(%s)",
                (node_run.id, [pl.id for pl in plate_locations]),
            )

    def get_user(self) -> NodeRun | None:
        if self.in_use_by is None:
            return None

        return NodeRun.fetch_from_id(self.in_use_by)


class PlateLocationWithNodeRunStatus(PlateLocation):
    def __init__(
        self,
        id: str,
        type: str | None,
        in_use_by: int | None,
        instrument_id: int | None,
        parent_id: str | None,
        x_capacity: int | None,
        y_capacity: int | None,
        node_run_status: str | None,
    ):
        super().__init__(
            id, type, in_use_by, instrument_id, parent_id, x_capacity, y_capacity
        )
        self.node_run_status = node_run_status

    @classmethod
    def fetch_from_ids(cls, ids: list[str]) -> list[PlateLocationWithNodeRunStatus]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pl.*, nr.status
                FROM plate_locations pl
                LEFT JOIN node_runs nr ON pl.id = nr.node_id
                WHERE pl.id = ANY(%s)
                """,
                (ids,),
            )
            rows = cur.fetchall()
            return [cls(*row) for row in rows]
