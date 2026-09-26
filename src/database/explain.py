# src/database/explain.py
"""Capture PostgreSQL execution plans via EXPLAIN."""

import json
import re
from typing import Literal

from psycopg import Connection


# CONSTANTS

READ_KEYWORDS = {"SELECT", "TABLE", "VALUES", "WITH", "SHOW", "EXPLAIN"}
WRITE_KEYWORDS = {"INSERT", "UPDATE", "DELETE", "MERGE", "TRUNCATE"}


# QUERY CLASSIFICATION

def _strip_leading_comments(sql: str) -> str:
    """
    Remove leading whitespace and comments from a SQL string.

    Why: A user might send `-- find slow orders\\nSELECT ...`. If we
    just split on whitespace, the first token would be `--`, not
    `SELECT`, and classification would fail.

    Handles:
      - Line comments:  -- until end of line
      - Block comments: /* ... */
    """
    # Remove leading whitespace
    sql = sql.lstrip()

    while True:
        if sql.startswith("--"):
            # Line comment: skip to next newline
            newline = sql.find("\n")
            if newline == -1:
                return ""  # whole string was a comment
            sql = sql[newline + 1:].lstrip()
        elif sql.startswith("/*"):
            # Block comment: skip to closing */
            end = sql.find("*/")
            if end == -1:
                return ""  # unterminated comment
            sql = sql[end + 2:].lstrip()
        else:
            return sql


def _classify_query(sql: str) -> Literal["read", "write", "unknown"]:
    """
    Decide whether a SQL statement is safe to run with EXPLAIN ANALYZE.

    Returns:
        "read"    -> safe to ANALYZE
        "write"   -> NOT safe to ANALYZE
        "unknown" -> couldn't classify; caller should decide
    """
    cleaned = _strip_leading_comments(sql)
    if not cleaned:
        return "unknown"

    # First token, uppercased
    first_token = re.split(r"\s", cleaned, maxsplit=1)[0].upper()

    if first_token in WRITE_KEYWORDS:
        return "write"
    if first_token in READ_KEYWORDS:
        return "read"
    return "unknown"


# SQL BUILDING

def _build_explain_sql(sql: str, query_type: Literal["read", "write", "unknown"]) -> str:
    """
    Build the final EXPLAIN statement.

    Read queries get ANALYZE (which runs them).
    Write queries and unknown queries do NOT — estimates only.
    """
    if query_type == "read":
        options = "ANALYZE, BUFFERS, FORMAT JSON"
    else:
        # write or unknown → estimates only, never execute
        options = "BUFFERS, FORMAT JSON"

    # Ensure the original SQL ends without a trailing semicolon,
    # because we're going to wrap it. PostgreSQL rejects
    # `EXPLAIN SELECT 1; ;`
    trimmed = sql.strip().rstrip(";")

    return f"EXPLAIN ({options}) {trimmed}"


# PUBLIC API

def capture_plan(conn: Connection, sql: str) -> dict:
    """
    Run EXPLAIN on `sql` and return the parsed plan.

    The returned dict has this shape:
        {
            "query_type": "read" | "write" | "unknown",
            "explain_sql": "<the full EXPLAIN statement>",
            "plan": [ ... the raw JSON plan from PostgreSQL ... ],
            "warning": "<optional string if ANALYZE was skipped>"
        }

    Raises:
        psycopg.Error  — if PostgreSQL rejects the EXPLAIN statement
        ValueError     — if the SQL is empty
    """
    if not sql or not sql.strip():
        raise ValueError("Empty SQL statement")

    query_type = _classify_query(sql)
    explain_sql = _build_explain_sql(sql, query_type)

    with conn.cursor() as cur:
        cur.execute(explain_sql)
        row = cur.fetchone()

    # PostgreSQL returns one row with one JSON column.
    # psycopg auto-parses JSON columns into Python lists/dicts.
    raw_plan = row[0]

    result = {
        "query_type": query_type,
        "explain_sql": explain_sql,
        "plan": raw_plan,
    }

    if query_type != "read":
        result["warning"] = (
            f"Query was classified as '{query_type}'. "
            "EXPLAIN ANALYZE was skipped for safety; timings are estimates only."
        )

    return result