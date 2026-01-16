"""Tests for SQL diff engine."""

import pytest

from sql_diff_ui.diff_engine import (
    compare_sql,
    extract_components,
    normalize_sql,
)
from sql_diff_ui.models import DiffCategory, Severity


def test_normalize_sql():
    """Test SQL normalization."""
    sql = "select id,name from users where status='active'"
    normalized = normalize_sql(sql)

    assert "SELECT" in normalized
    assert "FROM" in normalized
    assert "WHERE" in normalized
    # Should be pretty-printed with proper formatting
    assert "\n" in normalized


def test_extract_components_basic_select():
    """Test extracting components from basic SELECT query."""
    sql = "SELECT id, name, email FROM users WHERE status = 'active' ORDER BY created_at DESC"
    components = extract_components(sql)

    assert "id" in components.select_expressions
    assert "name" in components.select_expressions
    assert "email" in components.select_expressions
    assert "users" in components.from_tables
    assert len(components.where_predicates) > 0
    assert len(components.order_by) == 1
    assert "created_at" in components.order_by[0]


def test_extract_components_with_joins():
    """Test extracting JOIN information."""
    sql = """
    SELECT u.id, u.name, o.total
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.status = 'active'
    """
    components = extract_components(sql)

    assert len(components.joins) == 1
    assert components.joins[0]["type"] == "LEFT"
    assert "orders" in components.joins[0]["table"]


def test_extract_components_with_group_by():
    """Test extracting GROUP BY and HAVING."""
    sql = """
    SELECT category, COUNT(*) as count
    FROM products
    GROUP BY category
    HAVING COUNT(*) > 5
    """
    components = extract_components(sql)

    assert "category" in components.group_by
    assert len(components.having_predicates) > 0


def test_compare_sql_select_column_added():
    """Test detecting added SELECT column."""
    sql_a = "SELECT id, name FROM users"
    sql_b = "SELECT id, name, email FROM users"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    assert len(result.notices) > 0
    select_notices = [n for n in result.notices if n.category == DiffCategory.SELECT]
    assert len(select_notices) == 1
    assert "email" in select_notices[0].summary
    assert "Added" in select_notices[0].summary


def test_compare_sql_select_column_removed():
    """Test detecting removed SELECT column."""
    sql_a = "SELECT id, name, email FROM users"
    sql_b = "SELECT id, name FROM users"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    assert len(result.notices) > 0
    select_notices = [n for n in result.notices if n.category == DiffCategory.SELECT]
    assert len(select_notices) == 1
    assert "email" in select_notices[0].summary
    assert "Removed" in select_notices[0].summary
    assert select_notices[0].severity == Severity.WARN


def test_compare_sql_where_predicate_added():
    """Test detecting added WHERE condition."""
    sql_a = "SELECT id FROM users WHERE status = 'active'"
    sql_b = "SELECT id FROM users WHERE status = 'active' AND role = 'admin'"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    where_notices = [n for n in result.notices if n.category == DiffCategory.WHERE]
    assert len(where_notices) > 0
    # Should detect the added role condition
    added_notices = [n for n in where_notices if "Added" in n.summary]
    assert len(added_notices) > 0


def test_compare_sql_where_predicate_removed():
    """Test detecting removed WHERE condition."""
    sql_a = "SELECT id FROM users WHERE status = 'active' AND role = 'admin'"
    sql_b = "SELECT id FROM users WHERE status = 'active'"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    where_notices = [n for n in result.notices if n.category == DiffCategory.WHERE]
    assert len(where_notices) > 0
    # Should detect the removed role condition
    removed_notices = [n for n in where_notices if "Removed" in n.summary]
    assert len(removed_notices) > 0
    assert removed_notices[0].severity == Severity.WARN


def test_compare_sql_join_added():
    """Test detecting added JOIN."""
    sql_a = "SELECT u.id, u.name FROM users u"
    sql_b = "SELECT u.id, u.name FROM users u LEFT JOIN orders o ON u.id = o.user_id"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    join_notices = [n for n in result.notices if n.category == DiffCategory.JOIN]
    assert len(join_notices) == 1
    assert "Added" in join_notices[0].summary
    assert "LEFT" in join_notices[0].summary


def test_compare_sql_join_type_changed():
    """Test detecting JOIN type change."""
    sql_a = "SELECT * FROM users u LEFT JOIN orders o ON u.id = o.user_id"
    sql_b = "SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    join_notices = [n for n in result.notices if n.category == DiffCategory.JOIN]
    # Should detect both removal of LEFT and addition of INNER
    assert len(join_notices) >= 2


def test_compare_sql_limit_changed():
    """Test detecting LIMIT change."""
    sql_a = "SELECT id FROM users LIMIT 10"
    sql_b = "SELECT id FROM users LIMIT 20"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    limit_notices = [n for n in result.notices if n.category == DiffCategory.LIMIT]
    assert len(limit_notices) == 1
    assert "Changed LIMIT" in limit_notices[0].summary


def test_compare_sql_order_by_added():
    """Test detecting ORDER BY addition."""
    sql_a = "SELECT id, name FROM users"
    sql_b = "SELECT id, name FROM users ORDER BY created_at DESC"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    order_notices = [n for n in result.notices if n.category == DiffCategory.ORDER_BY]
    assert len(order_notices) == 1
    assert "Added" in order_notices[0].summary


def test_compare_sql_parse_error_fallback():
    """Test that parse errors are handled gracefully."""
    sql_a = "SELECT id FROM users"
    sql_b = "INVALID SQL QUERY @#$%"

    result = compare_sql(sql_a, sql_b, semantic_diff=True)

    # Should have a parse error notice
    assert result.parse_error is not None
    assert len(result.notices) > 0
    general_notices = [n for n in result.notices if n.category == DiffCategory.GENERAL]
    assert len(general_notices) > 0
    assert general_notices[0].severity == Severity.WARN

    # Should still have text diff
    assert result.text_diff is not None


def test_compare_sql_identical_queries():
    """Test comparing identical queries."""
    sql = "SELECT id, name FROM users WHERE status = 'active'"

    result = compare_sql(sql, sql, semantic_diff=True)

    # Should have no notices
    assert len(result.notices) == 0


def test_compare_sql_normalization_option():
    """Test that normalization option works."""
    sql_a = "select id from users"
    sql_b = "SELECT id FROM users"

    # With normalization, should be identical
    result_normalized = compare_sql(sql_a, sql_b, normalize=True, semantic_diff=True)
    assert len(result_normalized.notices) == 0

    # Without normalization (but semantic diff still works due to parsing)
    result_no_norm = compare_sql(sql_a, sql_b, normalize=False, semantic_diff=True)
    # Should still match semantically even without normalization
    assert len(result_no_norm.notices) == 0


def test_text_diff_generation():
    """Test that text diff is generated."""
    sql_a = "SELECT id FROM users"
    sql_b = "SELECT id, name FROM users"

    result = compare_sql(sql_a, sql_b, semantic_diff=False)

    # Should have a text diff
    assert result.text_diff
    assert "---" in result.text_diff or "+++" in result.text_diff or len(result.text_diff) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
