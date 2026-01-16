"""Core diff engine for comparing SQL queries."""

import difflib

import sqlglot
from sqlglot import exp

from .models import (
    ComparisonResult,
    DiffCategory,
    DiffNotice,
    Severity,
    SQLComponents,
)


def normalize_sql(sql: str, dialect: str = "auto") -> str:
    """
    Normalize SQL string using sqlglot.

    Args:
        sql: The SQL query string to normalize
        dialect: SQL dialect to use for parsing

    Returns:
        Normalized SQL string

    Raises:
        sqlglot.errors.ParseError: If SQL cannot be parsed
    """
    # Use None for auto-detection (empty string is sqlglot's default)
    dialect_arg = None if dialect == "auto" else dialect
    parsed = sqlglot.parse_one(sql, dialect=dialect_arg)
    return parsed.sql(pretty=True, normalize=True)


def extract_components(sql: str, dialect: str = "auto") -> SQLComponents:
    """
    Extract structured components from SQL query.

    Args:
        sql: The SQL query string
        dialect: SQL dialect to use for parsing

    Returns:
        SQLComponents with all extracted parts

    Raises:
        sqlglot.errors.ParseError: If SQL cannot be parsed
    """
    # Use None for auto-detection (empty string is sqlglot's default)
    dialect_arg = None if dialect == "auto" else dialect
    parsed = sqlglot.parse_one(sql, dialect=dialect_arg)

    # Extract SELECT expressions
    select_expressions = []
    if isinstance(parsed, exp.Select):
        for expr in parsed.expressions:
            if expr.alias:
                select_expressions.append(f"{expr.this.sql()} AS {expr.alias}")
            else:
                select_expressions.append(expr.sql())

    # Extract FROM tables
    from_tables = []
    if parsed.args.get("from_"):
        from_expr = parsed.args["from_"]
        if from_expr.this:
            from_tables.append(from_expr.this.sql())

    # Extract JOINs
    joins = []
    if parsed.args.get("joins"):
        for join in parsed.args["joins"]:
            join_info = {
                "type": join.side if join.side else "INNER",
                "table": join.this.sql(),
                "on": join.args.get("on").sql() if join.args.get("on") else "",
            }
            joins.append(join_info)

    # Extract WHERE predicates
    where_predicates = []
    if parsed.args.get("where"):
        where_expr = parsed.args["where"].this
        where_predicates = _split_predicates(where_expr)

    # Extract GROUP BY
    group_by = []
    if parsed.args.get("group"):
        group_expr = parsed.args["group"]
        for expr in group_expr.expressions:
            group_by.append(expr.sql())

    # Extract HAVING predicates
    having_predicates = []
    if parsed.args.get("having"):
        having_expr = parsed.args["having"].this
        having_predicates = _split_predicates(having_expr)

    # Extract ORDER BY
    order_by = []
    if parsed.args.get("order"):
        order_expr = parsed.args["order"]
        for expr in order_expr.expressions:
            direction = "DESC" if expr.args.get("desc") else "ASC"
            order_by.append(f"{expr.this.sql()} {direction}")

    # Extract LIMIT and OFFSET
    limit = None
    offset = None
    if parsed.args.get("limit"):
        limit = parsed.args["limit"].sql()
    if parsed.args.get("offset"):
        offset = parsed.args["offset"].sql()

    # Extract subqueries
    subqueries = _extract_subqueries(parsed)

    return SQLComponents(
        select_expressions=select_expressions,
        from_tables=from_tables,
        joins=joins,
        where_predicates=where_predicates,
        group_by=group_by,
        having_predicates=having_predicates,
        order_by=order_by,
        limit=limit,
        offset=offset,
        subqueries=subqueries,
    )


def _split_predicates(expr: exp.Expression) -> list[str]:
    """Split AND-joined predicates into individual conditions."""
    predicates = []

    if isinstance(expr, exp.And):
        # Recursively split AND expressions
        predicates.extend(_split_predicates(expr.left))
        predicates.extend(_split_predicates(expr.right))
    else:
        predicates.append(expr.sql())

    return predicates


def _extract_subqueries(parsed: exp.Expression) -> list[dict[str, str]]:
    """
    Extract all subqueries from a SQL expression.
    
    Args:
        parsed: The parsed SQL expression
        
    Returns:
        List of subquery dicts with location and SQL
    """
    subqueries = []
    
    # Find all Subquery nodes in the AST
    for subquery in parsed.find_all(exp.Subquery):
        # Determine the location context
        location = "UNKNOWN"
        parent = subquery.parent
        
        # Walk up the tree to find meaningful context
        if parent:
            # Check immediate parent
            if isinstance(parent, exp.In):
                location = "WHERE-IN"
            elif isinstance(parent, exp.Exists):
                location = "WHERE-EXISTS"
            elif isinstance(parent, exp.Where):
                location = "WHERE"
            elif isinstance(parent, exp.From):
                location = "FROM"
            elif isinstance(parent, exp.Join):
                location = "JOIN"
            elif isinstance(parent, exp.Having):
                location = "HAVING"
            else:
                # Check if it's a scalar subquery in SELECT (parent would be Alias or Column)
                grandparent = parent.parent if hasattr(parent, 'parent') else None
                if grandparent and isinstance(grandparent, exp.Select):
                    location = "SELECT"
                # Check ancestors for SELECT context
                elif any(isinstance(ancestor, exp.Select) for ancestor in subquery.walk(bfs=False)):
                    # If nested in select expressions, it's likely a scalar subquery
                    if not isinstance(parent, (exp.Where, exp.From, exp.Join, exp.Having)):
                        location = "SELECT"
        
        subqueries.append({
            "location": location,
            "sql": subquery.this.sql() if subquery.this else subquery.sql(),
        })
    
    return subqueries


def generate_text_diff(
    sql_a: str,
    sql_b: str,
    ignore_whitespace: bool = False,
) -> str:
    """
    Generate unified text diff between two SQL strings.

    Args:
        sql_a: First SQL query
        sql_b: Second SQL query
        ignore_whitespace: If True, ignore whitespace differences

    Returns:
        Unified diff string with colored annotations
    """
    lines_a = sql_a.splitlines(keepends=True)
    lines_b = sql_b.splitlines(keepends=True)

    if ignore_whitespace:
        lines_a = [line.strip() + "\n" for line in lines_a if line.strip()]
        lines_b = [line.strip() + "\n" for line in lines_b if line.strip()]

    diff = difflib.unified_diff(
        lines_a,
        lines_b,
        fromfile="SQL A",
        tofile="SQL B",
        lineterm="",
    )

    return "\n".join(diff)


def generate_semantic_notices(
    components_a: SQLComponents,
    components_b: SQLComponents,
) -> list[DiffNotice]:
    """
    Generate human-friendly notices from component comparison.

    Args:
        components_a: Components from SQL A
        components_b: Components from SQL B

    Returns:
        List of DiffNotice objects describing changes
    """
    notices = []

    # Compare SELECT expressions
    select_added = set(components_b.select_expressions) - set(components_a.select_expressions)
    select_removed = set(components_a.select_expressions) - set(components_b.select_expressions)

    for expr in select_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.SELECT,
                summary=f"Removed column/expression: {_truncate(expr)}",
                severity=Severity.WARN,
            )
        )

    for expr in select_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.SELECT,
                summary=f"Added column/expression: {_truncate(expr)}",
                severity=Severity.INFO,
            )
        )

    # Compare FROM tables
    from_added = set(components_b.from_tables) - set(components_a.from_tables)
    from_removed = set(components_a.from_tables) - set(components_b.from_tables)

    for table in from_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.FROM,
                summary=f"Removed FROM table: {table}",
                severity=Severity.WARN,
            )
        )

    for table in from_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.FROM,
                summary=f"Added FROM table: {table}",
                severity=Severity.INFO,
            )
        )

    # Compare JOINs
    joins_a_set = {_join_signature(j) for j in components_a.joins}
    joins_b_set = {_join_signature(j) for j in components_b.joins}

    joins_added = joins_b_set - joins_a_set
    joins_removed = joins_a_set - joins_b_set

    for join_sig in joins_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.JOIN,
                summary=f"Removed JOIN: {join_sig}",
                severity=Severity.WARN,
            )
        )

    for join_sig in joins_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.JOIN,
                summary=f"Added JOIN: {join_sig}",
                severity=Severity.INFO,
            )
        )

    # Compare WHERE predicates
    where_added = set(components_b.where_predicates) - set(components_a.where_predicates)
    where_removed = set(components_a.where_predicates) - set(components_b.where_predicates)

    for pred in where_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.WHERE,
                summary=f"Removed WHERE condition: {_truncate(pred)}",
                severity=Severity.WARN,
            )
        )

    for pred in where_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.WHERE,
                summary=f"Added WHERE condition: {_truncate(pred)}",
                severity=Severity.INFO,
            )
        )

    # Compare GROUP BY
    group_added = set(components_b.group_by) - set(components_a.group_by)
    group_removed = set(components_a.group_by) - set(components_b.group_by)

    for col in group_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.GROUP_BY,
                summary=f"Removed GROUP BY column: {col}",
                severity=Severity.WARN,
            )
        )

    for col in group_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.GROUP_BY,
                summary=f"Added GROUP BY column: {col}",
                severity=Severity.INFO,
            )
        )

    # Compare HAVING
    having_added = set(components_b.having_predicates) - set(components_a.having_predicates)
    having_removed = set(components_a.having_predicates) - set(components_b.having_predicates)

    for pred in having_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.HAVING,
                summary=f"Removed HAVING condition: {_truncate(pred)}",
                severity=Severity.WARN,
            )
        )

    for pred in having_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.HAVING,
                summary=f"Added HAVING condition: {_truncate(pred)}",
                severity=Severity.INFO,
            )
        )

    # Compare ORDER BY
    order_added = set(components_b.order_by) - set(components_a.order_by)
    order_removed = set(components_a.order_by) - set(components_b.order_by)

    for col in order_removed:
        notices.append(
            DiffNotice(
                category=DiffCategory.ORDER_BY,
                summary=f"Removed ORDER BY: {col}",
                severity=Severity.INFO,
            )
        )

    for col in order_added:
        notices.append(
            DiffNotice(
                category=DiffCategory.ORDER_BY,
                summary=f"Added ORDER BY: {col}",
                severity=Severity.INFO,
            )
        )

    # Compare LIMIT/OFFSET
    if components_a.limit != components_b.limit:
        if components_a.limit and not components_b.limit:
            notices.append(
                DiffNotice(
                    category=DiffCategory.LIMIT,
                    summary=f"Removed LIMIT {components_a.limit}",
                    severity=Severity.INFO,
                )
            )
        elif not components_a.limit and components_b.limit:
            notices.append(
                DiffNotice(
                    category=DiffCategory.LIMIT,
                    summary=f"Added LIMIT {components_b.limit}",
                    severity=Severity.INFO,
                )
            )
        else:
            notices.append(
                DiffNotice(
                    category=DiffCategory.LIMIT,
                    summary=f"Changed LIMIT from {components_a.limit} to {components_b.limit}",
                    severity=Severity.INFO,
                )
            )

    if components_a.offset != components_b.offset:
        if components_a.offset and not components_b.offset:
            notices.append(
                DiffNotice(
                    category=DiffCategory.LIMIT,
                    summary=f"Removed OFFSET {components_a.offset}",
                    severity=Severity.INFO,
                )
            )
        elif not components_a.offset and components_b.offset:
            notices.append(
                DiffNotice(
                    category=DiffCategory.LIMIT,
                    summary=f"Added OFFSET {components_b.offset}",
                    severity=Severity.INFO,
                )
            )
        else:
            notices.append(
                DiffNotice(
                    category=DiffCategory.LIMIT,
                    summary=f"Changed OFFSET from {components_a.offset} to {components_b.offset}",
                    severity=Severity.INFO,
                )
            )

    # Compare subqueries - group by location for better reporting
    subqueries_a_by_location = {}
    for sq in components_a.subqueries:
        loc = sq["location"]
        if loc not in subqueries_a_by_location:
            subqueries_a_by_location[loc] = []
        subqueries_a_by_location[loc].append(sq["sql"])

    subqueries_b_by_location = {}
    for sq in components_b.subqueries:
        loc = sq["location"]
        if loc not in subqueries_b_by_location:
            subqueries_b_by_location[loc] = []
        subqueries_b_by_location[loc].append(sq["sql"])

    # Check each location for changes
    all_locations = set(subqueries_a_by_location.keys()) | set(
        subqueries_b_by_location.keys()
    )

    for location in all_locations:
        sqs_a = set(subqueries_a_by_location.get(location, []))
        sqs_b = set(subqueries_b_by_location.get(location, []))

        removed = sqs_a - sqs_b
        added = sqs_b - sqs_a

        # Report removed subqueries
        for sq_sql in removed:
            count_a = subqueries_a_by_location.get(location, []).count(sq_sql)
            summary = f"Removed subquery in {location}"
            if count_a > 1:
                summary += f" ({count_a} occurrences)"
            notices.append(
                DiffNotice(
                    category=DiffCategory.SUBQUERY,
                    summary=summary,
                    details=_truncate(sq_sql, 150),
                    severity=Severity.WARN,
                )
            )

        # Report added subqueries
        for sq_sql in added:
            count_b = subqueries_b_by_location.get(location, []).count(sq_sql)
            summary = f"Added subquery in {location}"
            if count_b > 1:
                summary += f" ({count_b} occurrences)"
            notices.append(
                DiffNotice(
                    category=DiffCategory.SUBQUERY,
                    summary=summary,
                    details=_truncate(sq_sql, 150),
                    severity=Severity.INFO,
                )
            )

    # Report location-level changes (subquery count differences in same location)
    for location in all_locations:
        count_a = len(subqueries_a_by_location.get(location, []))
        count_b = len(subqueries_b_by_location.get(location, []))
        
        if count_a != count_b and count_a > 0 and count_b > 0:
            # Only report if there are subqueries in both but counts differ
            if count_b > count_a:
                notices.append(
                    DiffNotice(
                        category=DiffCategory.SUBQUERY,
                        summary=f"Increased subquery count in {location}: {count_a} → {count_b}",
                        severity=Severity.INFO,
                    )
                )
            else:
                notices.append(
                    DiffNotice(
                        category=DiffCategory.SUBQUERY,
                        summary=f"Decreased subquery count in {location}: {count_a} → {count_b}",
                        severity=Severity.WARN,
                    )
                )

    return notices


def _join_signature(join: dict[str, str]) -> str:
    """Create a comparable signature for a JOIN."""
    return f"{join['type']} JOIN {join['table']} ON {join['on']}"


def _subquery_signature(subquery: dict[str, str]) -> str:
    """Create a comparable signature for a subquery."""
    return f"{subquery['location']}: {subquery['sql']}"


def _truncate(text: str, max_len: int = 60) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def compare_sql(
    sql_a: str,
    sql_b: str,
    normalize: bool = True,
    ignore_whitespace: bool = True,
    case_insensitive_keywords: bool = True,
    semantic_diff: bool = True,
    dialect: str = "auto",
) -> ComparisonResult:
    """
    Compare two SQL queries and generate comprehensive diff results.

    Args:
        sql_a: First SQL query
        sql_b: Second SQL query
        normalize: Whether to normalize SQL before comparison
        ignore_whitespace: Whether to ignore whitespace in text diff
        case_insensitive_keywords: Whether to treat keywords case-insensitively
        semantic_diff: Whether to perform semantic/structural diff
        dialect: SQL dialect for parsing

    Returns:
        ComparisonResult with text diff and semantic notices
    """
    notices = []
    sql_a_normalized = None
    sql_b_normalized = None
    parse_error = None

    # Prepare SQL strings for comparison
    compare_a = sql_a
    compare_b = sql_b

    if case_insensitive_keywords:
        # This is handled by sqlglot normalization if enabled
        pass

    # Attempt semantic diff if enabled
    if semantic_diff:
        try:
            if normalize:
                sql_a_normalized = normalize_sql(sql_a, dialect=dialect)
                sql_b_normalized = normalize_sql(sql_b, dialect=dialect)
                compare_a = sql_a_normalized
                compare_b = sql_b_normalized

            components_a = extract_components(compare_a, dialect=dialect)
            components_b = extract_components(compare_b, dialect=dialect)
            notices = generate_semantic_notices(components_a, components_b)

        except Exception as e:
            parse_error = f"Semantic diff unavailable: {type(e).__name__}: {str(e)}"
            notices = [
                DiffNotice(
                    category=DiffCategory.GENERAL,
                    summary="Parse error - semantic diff unavailable",
                    details=parse_error,
                    severity=Severity.WARN,
                )
            ]

    # Generate text diff
    text_diff = generate_text_diff(compare_a, compare_b, ignore_whitespace=ignore_whitespace)

    return ComparisonResult(
        text_diff=text_diff,
        notices=notices,
        sql_a_normalized=sql_a_normalized,
        sql_b_normalized=sql_b_normalized,
        parse_error=parse_error,
    )
