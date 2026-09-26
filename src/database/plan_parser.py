# src/database/plan_parser.py
"""Parse PostgreSQL EXPLAIN (FORMAT JSON) output into structured nodes."""

from typing import List, Optional, Dict, Any

from src.core.models import PlanNode


# ============================================================
# JSON FIELD MAPPING
# ============================================================
# PostgreSQL's JSON keys use spaces ("Node Type", "Actual Total Time").
# Our PlanNode dataclass uses snake_case ("node_type", "actual_total_time_ms").
# This dict maps one to the other so we don't hardcode strings everywhere.

_FIELD_MAP = {
    "node_type": "Node Type",
    "relation_name": "Relation Name",
    "startup_cost": "Startup Cost",
    "total_cost": "Total Cost",
    "plan_rows": "Plan Rows",
    "actual_startup_time_ms": "Actual Startup Time",
    "actual_total_time_ms": "Actual Total Time",
    "actual_rows": "Actual Rows",
    "actual_loops": "Actual Loops",
    "filter_condition": "Filter",
    "rows_removed_by_filter": "Rows Removed by Filter",
}


# ============================================================
# PARSING
# ============================================================

def _walk_plan(json_node: Dict[str, Any], nodes: List[PlanNode]) -> PlanNode:
    """
    Recursively walk one node of the JSON plan tree.

    Creates a PlanNode from this JSON node, recurses into each child,
    and appends the resulting PlanNode to the flat `nodes` list.

    Returns the PlanNode it created (so the parent can attach it as
    a child).
    """
    # Build the PlanNode, pulling each field from the JSON using
    # the field map. Default to None / 0 / [] if missing.
    node = PlanNode(
        node_type=json_node.get(_FIELD_MAP["node_type"], "Unknown"),
        relation_name=json_node.get(_FIELD_MAP["relation_name"]),
        startup_cost=json_node.get(_FIELD_MAP["startup_cost"], 0.0),
        total_cost=json_node.get(_FIELD_MAP["total_cost"], 0.0),
        plan_rows=json_node.get(_FIELD_MAP["plan_rows"], 0),
        actual_startup_time_ms=json_node.get(_FIELD_MAP["actual_startup_time_ms"]),
        actual_total_time_ms=json_node.get(_FIELD_MAP["actual_total_time_ms"]),
        actual_rows=json_node.get(_FIELD_MAP["actual_rows"]),
        actual_loops=json_node.get(_FIELD_MAP["actual_loops"]),
        filter_condition=json_node.get(_FIELD_MAP["filter_condition"]),
        rows_removed_by_filter=json_node.get(_FIELD_MAP["rows_removed_by_filter"]),
        child_nodes=[],
    )

    # Recurse into children. PostgreSQL nests children under "Plans".
    # Note: we create a fresh list per node — no shared mutable state.
    for child_json in json_node.get("Plans", []):
        child_node = _walk_plan(child_json, nodes)
        node.child_nodes.append(child_node)

    # Add this node to the flat list AFTER its children.
    # Leaves end up earlier in the list, which matches the intuition
    # that leaves are where time is usually spent.
    nodes.append(node)
    return node


def parse_plan(raw_json: Any) -> List[PlanNode]:
    """
    Parse the JSON output from EXPLAIN (FORMAT JSON) into a flat
    list of PlanNode objects.

    PostgreSQL returns the plan as a single-element list:
        [ { "Plan": {...}, "Planning Time": ..., "Execution Time": ... } ]

    Raises:
        ValueError — if the JSON doesn't have the expected shape.
    """
    # Normalize: EXPLAIN returns a list of one element. If we already
    # got a dict (some drivers unwrap it), handle both.
    if isinstance(raw_json, list):
        if not raw_json:
            raise ValueError("Empty EXPLAIN output")
        outer = raw_json[0]
    elif isinstance(raw_json, dict):
        outer = raw_json
    else:
        raise ValueError(f"Unexpected EXPLAIN output type: {type(raw_json)}")

    root = outer.get("Plan")
    if not root:
        raise ValueError("EXPLAIN output missing 'Plan' key")

    nodes: List[PlanNode] = []
    _walk_plan(root, nodes)
    return nodes


# ============================================================
# BOTTLENECK DETECTION
# ============================================================

def identify_bottleneck(nodes: List[PlanNode]) -> Optional[PlanNode]:
    """
    Return the node that consumed the most time.

    Uses `actual_total_time_ms` when available (EXPLAIN ANALYZE was run).
    Falls back to `total_cost` when only estimates are available
    (write queries or plain EXPLAIN).

    Returns None if there are no nodes.
    """
    if not nodes:
        return None

    # Prefer measured time. Filter out nodes without it.
    with_time = [n for n in nodes if n.actual_total_time_ms is not None]
    if with_time:
        return max(with_time, key=lambda n: n.actual_total_time_ms)

    # Fall back to cost estimates.
    return max(nodes, key=lambda n: n.total_cost)


# ============================================================
# SUMMARY FORMATTING
# ============================================================

def summarize_node(node: PlanNode) -> str:
    """
    Produce a one-line human-readable summary of a plan node.

    Example: "Seq Scan on orders (5,000,000 rows scanned, 45.79 ms)"
    """
    parts = [node.node_type]
    if node.relation_name:
        parts.append(f"on {node.relation_name}")

    details = []
    if node.actual_rows is not None:
        details.append(f"{node.actual_rows:,} rows")
    elif node.plan_rows:
        details.append(f"~{node.plan_rows:,} rows estimated")

    if node.actual_total_time_ms is not None:
        details.append(f"{node.actual_total_time_ms:.2f} ms")

    if details:
        return f"{' '.join(parts)} ({', '.join(details)})"
    return " ".join(parts)


def analyze_plan(raw_json: Any) -> Dict[str, Any]:
    """
    Main entry point. Parses the plan, identifies the bottleneck, and
    returns a structured summary.

    The returned dict is what the analyzer layer consumes next.

    Shape:
        {
            "all_nodes": List[PlanNode],
            "bottleneck": PlanNode | None,
            "bottleneck_summary": str,
            "node_count": int,
        }
    """
    nodes = parse_plan(raw_json)
    bottleneck = identify_bottleneck(nodes)

    return {
        "all_nodes": nodes,
        "bottleneck": bottleneck,
        "bottleneck_summary": summarize_node(bottleneck) if bottleneck else "",
        "node_count": len(nodes),
    }