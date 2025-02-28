from __future__ import annotations

import logging
from psycopg import connect

logger = logging.getLogger(__name__)

logger.info(f"Connecting to database")
conn = connect("postgres://vestradb_user:veggie_straws@127.0.0.1:5432/vestradb")
logger.info(f"Connected to database")
