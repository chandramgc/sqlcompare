"""Test multiple subquery handling."""

import pytest

from sql_diff_ui.diff_engine import compare_sql, extract_components
from sql_diff_ui.models import DiffCategory


def test_extract_subqueries_in_where():
    """Test extracting subqueries from WHERE clause."""
    sql = """
    SELECT id, name 
    FROM users 
    WHERE id IN (SELECT user_id FROM orders WHERE status = 'active')
    """
    components = extract_components(sql)
    
    assert len(components.subqueries) == 1
    assert components.subqueries[0]["location"] == "WHERE-IN"


def test_extract_multiple_subqueries_in_select():
    """Test extracting multiple scalar subqueries from SELECT."""
    sql = """
    SELECT 
        id, 
        name,
        (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count,
        (SELECT MAX(created_at) FROM orders WHERE user_id = users.id) as last_order
    FROM users
    """
    components = extract_components(sql)
    
    assert len(components.subqueries) == 2
    # Both should be identified as SELECT subqueries
    assert all(sq["location"] == "SELECT" for sq in components.subqueries)


def test_compare_subquery_added():
    """Test detecting added subquery."""
    sql_a = "SELECT id, name FROM users"
    sql_b = """
    SELECT 
        id, 
        name,
        (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count
    FROM users
    """
    
    result = compare_sql(sql_a, sql_b, semantic_diff=True)
    subquery_notices = [n for n in result.notices if n.category == DiffCategory.SUBQUERY]
    
    assert len(subquery_notices) >= 1
    assert any("Added subquery" in n.summary for n in subquery_notices)


def test_compare_subquery_removed():
    """Test detecting removed subquery."""
    sql_a = """
    SELECT 
        id, 
        name,
        (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count
    FROM users
    """
    sql_b = "SELECT id, name FROM users"
    
    result = compare_sql(sql_a, sql_b, semantic_diff=True)
    subquery_notices = [n for n in result.notices if n.category == DiffCategory.SUBQUERY]
    
    assert len(subquery_notices) >= 1
    assert any("Removed subquery" in n.summary for n in subquery_notices)


def test_compare_multiple_subqueries_changed():
    """Test detecting changes in multiple subqueries."""
    sql_a = """
    SELECT 
        id, 
        (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count
    FROM users
    """
    sql_b = """
    SELECT 
        id, 
        (SELECT COUNT(*) FROM orders WHERE user_id = users.id AND status = 'active') as order_count,
        (SELECT SUM(total) FROM orders WHERE user_id = users.id) as total_spent
    FROM users
    """
    
    result = compare_sql(sql_a, sql_b, semantic_diff=True)
    subquery_notices = [n for n in result.notices if n.category == DiffCategory.SUBQUERY]
    
    # Should detect removed old subquery, added modified subquery, and added new subquery
    assert len(subquery_notices) >= 2
    
    # Should report increased count
    assert any("Increased subquery count" in n.summary for n in subquery_notices)


def test_subquery_in_from_clause():
    """Test subquery in FROM clause (derived table)."""
    sql_a = """
    SELECT dept_name, avg_salary
    FROM (
        SELECT department as dept_name, AVG(salary) as avg_salary
        FROM employees
        GROUP BY department
    ) dept_stats
    """
    sql_b = """
    SELECT dept_name, avg_salary, employee_count
    FROM (
        SELECT department as dept_name, AVG(salary) as avg_salary, COUNT(*) as employee_count
        FROM employees
        GROUP BY department
    ) dept_stats
    """
    
    result = compare_sql(sql_a, sql_b, semantic_diff=True)
    
    # Should detect SELECT column change and subquery modification
    assert len(result.notices) > 0
    
    components_a = extract_components(sql_a)
    components_b = extract_components(sql_b)
    
    # Both should have FROM subqueries
    assert len(components_a.subqueries) >= 1
    assert len(components_b.subqueries) >= 1
    assert any(sq["location"] == "FROM" for sq in components_a.subqueries)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
