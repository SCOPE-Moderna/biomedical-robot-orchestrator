from __future__ import annotations

from .node_runs import NodeRun
from .conn import conn


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
    def fetch_from_ids(
        cls, ids: list[str], join_node_runs_status
    ) -> list[PlateLocation]:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM plate_locations WHERE id = ANY(%s)",
                (ids,),
            )
            rows = cur.fetchall()
            return [cls(*row) for row in rows]
        
    @classmethod
    def create(cls, instrument_id: int, x_capacity: int = 1, y_capacity: int = 1) -> PlateLocation:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO plate_locations (instrument_id, x_capacity, y_capacity) "
                "VALUES (%d, %d, %d) "
                "RETURNING id",
                (int(instrument_id), x_capacity, y_capacity),
            )
            [plate_loc_id, type, in_use_by, instrument_id, parent_id, x_capacity, y_capacity] = cur.fetchone()
            return cls(
                plate_loc_id,
                type,
                in_use_by,
                instrument_id,
                parent_id,
                x_capacity,
                y_capacity,
            )

    def set_in_use_by(self, node_run_id: int | None, node_run: NodeRun | None):
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
