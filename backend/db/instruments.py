from __future__ import annotations

from .node_runs import NodeRun
from .conn import conn
import datetime as dt


class Instrument:
    def __init__(
            self,
            id: int,
            name: str,
            type: str,
            connection_method: str,
            connection_info: str | None,
            in_use_by: int | None,
            created_at: dt.datetime,
            updated_at: dt.datetime,
    ):
        self.id = id
        self.name = name
        self.type = type
        self.connection_method = connection_method
        self.connection_info = connection_info
        self.in_use_by = in_use_by
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def fetch_from_id(cls, id: int) -> Instrument:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM instruments WHERE id = %s", (id,))
            row = cur.fetchone()
            return cls(*row)
    
    @classmethod
    def create(cls, name: str = "xpeel_1", type: str = "xpeel", connection_method: str = "serial") -> Instrument:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO instruments (name, type, connection_method, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING id, name, type, connection_method, connection_info, in_use_by, created_at, updated_at",
                (name, type, connection_method, f'{dt.datetime.now()}', f'{dt.datetime.now()}'),
            )
            [instrument_id, name, type, connection_method, connection_info, in_use_by, created_at, updated_at] = cur.fetchone()
            return cls(
                instrument_id,
                name,
                type,
                connection_method,
                connection_info,
                in_use_by,
                created_at,
                updated_at,
            )
        
    def set_in_use_by(self, node_run_id: int | None, node_run: NodeRun | None):
        if node_run is not None:
            node_run_id = node_run.id

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE instruments SET in_use_by = %s WHERE id = %s",
                (node_run_id, self.id),
            )

    def get_user(self) -> NodeRun | None:
        if self.in_use_by is None:
            return None

        return NodeRun.fetch_from_id(self.in_use_by)
