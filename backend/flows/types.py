from typing import TypedDict


class RawNode(TypedDict):
    id: str
    type: str
    wires: list[list[str]] | None
