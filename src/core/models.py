# src/core/models.py
"""Data models (dataclasses) used throughout the application."""

from dataclasses import dataclass, field
from typing import Optional, List, Literal, Dict, Any


@dataclass
class PlanNode:
    """A single node from a PostgreSQL execution plan."""
    node_type: str
    relation_name: Optional[str] = None
    startup_cost: float = 0.0
    total_cost: float = 0.0
    plan_rows: int = 0
    actual_startup_time_ms: Optional[float] = None
    actual_total_time_ms: Optional[float] = None
    actual_rows: Optional[int] = None
    actual_loops: Optional[int] = None
    filter_condition: Optional[str] = None
    rows_removed_by_filter: Optional[int] = None
    child_nodes: List["PlanNode"] = field(default_factory=list)


@dataclass
class Diagnosis:
    """Result of deterministic analysis."""
    problem: Literal[
        "seq_scan", "missing_index", "bad_join", "nested_loop",
        "hash_join", "sort_expensive", "aggregate_expensive",
        "statistics_off", "unknown"
    ]
    table: str
    columns: List[str]
    rows_estimated: int
    current_plan_summary: str
    suggested_fix_description: str
    rows_actual: Optional[int] = None
    bottleneck_node: Optional[PlanNode] = None


@dataclass
class Candidate:
    """LLM-generated or rule-generated candidate fix."""
    type: Literal["index", "rewrite"]
    sql: str
    reasoning: str
    confidence: Optional[float] = None
    source: Literal["rule", "llm"] = "rule"


@dataclass
class BenchmarkResult:
    """Result of running a benchmark."""
    mode: Literal["fast", "full"]
    execution_time_ms: float
    cold_cache_ms: Optional[float] = None
    warm_cache_ms: Optional[float] = None
    trials: Optional[List[float]] = None
    median_ms: Optional[float] = None
    variance: Optional[float] = None


@dataclass
class RegressionCheck:
    """Result of HypoPG regression check."""
    passed: bool
    affected_queries: List[Dict[str, Any]]
    warnings: List[str]


@dataclass
class OptimizationResult:
    """Final output of the optimizer."""
    query: str
    diagnosis: Diagnosis
    candidate: Candidate
    before: BenchmarkResult
    after: BenchmarkResult
    regression_check: Optional[RegressionCheck] = None
    improvement_pct: float = 0.0
    accepted: bool = False
    migration_sql: Optional[str] = None
    pr_url: Optional[str] = None