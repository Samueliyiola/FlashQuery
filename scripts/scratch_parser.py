# scripts/scratch_parser.py
"""Throwaway script to eyeball the parser on a real query."""

from src.database.connection import get_connection
from src.database.explain import capture_plan
from src.database.plan_parser import analyze_plan


with get_connection() as conn:
    result = capture_plan(conn, "SELECT * FROM orders WHERE customer_id = 50000")

parsed = analyze_plan(result["plan"])

print(f"Query type:  {result['query_type']}")
print(f"Node count:  {parsed['node_count']}")
print(f"Bottleneck:  {parsed['bottleneck_summary']}")
print()
print("All nodes:")
for node in parsed["all_nodes"]:
    print(f"  - {node.node_type:15s} {node.relation_name or '':15s} "
          f"time={node.actual_total_time_ms} rows={node.actual_rows}")