from contextlib import contextmanager
from typing import Iterator, Optional

import psycopg
from psycopg import Connection

from src.core.config import config


def _build_conninfo(
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
    sslmode: str,
) -> str:
    return (
        f"host={host} "
        f"port={port} "
        f"dbname={dbname} "
        f"user={user} "
        f"password={password} "
        f"sslmode={sslmode}"
    )


@contextmanager
def get_connection(
    host: Optional[str] = None,
    port: Optional[int] = None,
    dbname: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
) -> Iterator[Connection]:

    conninfo = _build_conninfo(
        host=host or config.db_host,
        port=port or config.db_port,
        dbname=dbname or config.db_name,
        user=user or config.db_user,
        password=password or config.db_password,
        sslmode=config.db_sslmode
    )

    conn = psycopg.connect(conninfo)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def test_connection() -> dict:
    """
    Quick health check. Runs a trivial query and returns metadata
    about the PostgreSQL instance that I am  connected to.

    Returns a dict like:
        {
            "connected": True,
            "version": "PostgreSQL 16.1 ...",
            "database": "testdb",
            "user": "postgres",
        }

    If the connection fails, returns {"connected": False, "error": "..."}.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version(), current_database(), current_user;")
                row = cur.fetchone()
                return {
                    "connected": True,
                    "version": row[0],
                    "database": row[1],
                    "user": row[2]
                }
    except Exception as e:
        return {"connected": False, "error": str(e)}