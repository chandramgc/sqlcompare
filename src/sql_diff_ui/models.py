"""Data models for SQL diff results."""

from dataclasses import dataclass, field
from enum import Enum


class DiffCategory(str, Enum):
    """Category of SQL difference."""

    SELECT = "SELECT"
    FROM = "FROM"
    JOIN = "JOIN"
    WHERE = "WHERE"
    GROUP_BY = "GROUP_BY"
    HAVING = "HAVING"
    ORDER_BY = "ORDER_BY"
    LIMIT = "LIMIT"
    SUBQUERY = "SUBQUERY"
    GENERAL = "GENERAL"


class Severity(str, Enum):
    """Severity level of difference notice."""

    INFO = "INFO"
    WARN = "WARN"


@dataclass
class DiffNotice:
    """A single difference notice with human-friendly description."""

    category: DiffCategory
    summary: str
    details: str | None = None
    severity: Severity = Severity.INFO

    def __str__(self) -> str:
        """Format notice for display."""
        prefix = "⚠️" if self.severity == Severity.WARN else "ℹ️"
        text = f"{prefix} [{self.category.value}] {self.summary}"
        if self.details:
            text += f"\n   {self.details}"
        return text


@dataclass
class SQLComponents:
    """Structured components extracted from a SQL query."""

    select_expressions: list[str]
    from_tables: list[str]
    joins: list[dict[str, str]]  # [{"type": "LEFT", "table": "orders", "on": "..."}]
    where_predicates: list[str]
    group_by: list[str]
    having_predicates: list[str]
    order_by: list[str]
    limit: str | None = None
    offset: str | None = None
    subqueries: list[dict[str, str]] = field(default_factory=list)


@dataclass
class ComparisonResult:
    """Complete comparison result with text and semantic diffs."""

    text_diff: str
    notices: list[DiffNotice]
    sql_a_normalized: str | None = None
    sql_b_normalized: str | None = None
    parse_error: str | None = None
