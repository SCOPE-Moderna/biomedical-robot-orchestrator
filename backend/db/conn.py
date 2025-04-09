from __future__ import annotations

import logging
from os import getenv
from sys import exit
from psycopg import connect

logger = logging.getLogger(__name__)

logger.info(f"Connecting to database")

DATABASE_URL = getenv("DATABASE_URL")
if DATABASE_URL is None:
    logger.error("The DATABASE_URL environment variable is required.")
    exit(1)

conn = connect(DATABASE_URL)
conn.set_autocommit(True)
logger.info(f"Connected to database")
