"""Tests for SQL validator."""

import pytest

from sql_diff_ui.sql_validator import SQLValidator, ValidationError


class TestSQLValidator:
    """Test suite for SQLValidator."""

    def test_valid_simple_select(self):
        """Test validation of a simple valid SELECT query."""
        validator = SQLValidator()
        is_valid, errors = validator.validate_sql("SELECT * FROM users")

        assert is_valid is True
        assert len(errors) == 0

    def test_valid_complex_query(self):
        """Test validation of a complex valid query."""
        sql = """
        SELECT u.id, u.name, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        GROUP BY u.id, u.name
        HAVING COUNT(o.id) > 5
        ORDER BY order_count DESC
        LIMIT 10
        """
        validator = SQLValidator()
        is_valid, errors = validator.validate_sql(sql)

        assert is_valid is True
        assert len(errors) == 0

    def test_empty_sql(self):
        """Test validation of empty SQL."""
        validator = SQLValidator()
        is_valid, errors = validator.validate_sql("")

        assert is_valid is False
        assert len(errors) == 1
        assert "empty" in errors[0].message.lower()

    def test_invalid_syntax(self):
        """Test validation of SQL with syntax errors."""
        validator = SQLValidator()
        is_valid, errors = validator.validate_sql("SELECT * FORM users")

        assert is_valid is False
        assert len(errors) > 0

    def test_unbalanced_parentheses(self):
        """Test detection of unbalanced parentheses."""
        validator = SQLValidator()
        sql = "SELECT * FROM users WHERE (status = 'active' AND role = 'admin'"
        is_valid, errors = validator.validate_sql(sql)

        assert is_valid is False
        assert any("parentheses" in error.message.lower() for error in errors)

    def test_unbalanced_quotes(self):
        """Test detection of unbalanced quotes."""
        validator = SQLValidator()
        sql = "SELECT * FROM users WHERE name = 'John"
        is_valid, errors = validator.validate_sql(sql)

        assert is_valid is False
        # Should detect unbalanced quotes
        assert len(errors) > 0

    def test_beautify_simple_query(self):
        """Test beautification of a simple query."""
        validator = SQLValidator()
        sql = "select id,name from users where status='active'"
        beautified = validator.beautify_sql(sql)

        # Should be formatted with proper spacing and case
        assert beautified is not None
        assert len(beautified) > len(sql)

    def test_beautify_complex_query(self):
        """Test beautification of a complex query."""
        validator = SQLValidator()
        sql = "SELECT u.id,u.name,COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id=o.user_id GROUP BY u.id"
        beautified = validator.beautify_sql(sql)

        # Should be formatted with proper indentation
        assert beautified is not None
        assert "\n" in beautified  # Should have line breaks

    def test_beautify_invalid_sql(self):
        """Test that beautifying SQL with lost content raises an error."""
        validator = SQLValidator()

        # Test with SQL that loses content during parsing (missing comparison operator)
        sql = "SELECT * FROM users WHERE role 'admin'"
        with pytest.raises(ValueError):
            validator.beautify_sql(sql)

    def test_missing_comparison_operator(self):
        """Test detection of missing comparison operator."""
        validator = SQLValidator()
        sql = """
        SELECT id, name, phone
        FROM users
        WHERE status = 'active' AND role 'customer'
        """
        is_valid, errors = validator.validate_sql(sql)

        assert is_valid is False
        assert len(errors) > 0
        # Should detect lost string literal or incomplete comparison
        assert any("customer" in error.message.lower() or "syntax" in error.message.lower() 
                   for error in errors)

    def test_validate_and_beautify_valid(self):
        """Test combined validation and beautification of valid SQL."""
        validator = SQLValidator()
        sql = "select * from users where status='active'"

        is_valid, beautified, errors = validator.validate_and_beautify(sql)

        assert is_valid is True
        assert beautified != sql  # Should be beautified
        assert len(errors) == 0

    def test_validate_and_beautify_invalid(self):
        """Test combined validation and beautification of invalid SQL."""
        validator = SQLValidator()
        sql = "SELECT * FORM users"

        is_valid, beautified, errors = validator.validate_and_beautify(sql)

        assert is_valid is False
        assert beautified == sql  # Should return original
        assert len(errors) > 0

    def test_dialect_specific_validation(self):
        """Test validation with specific SQL dialect."""
        validator = SQLValidator(dialect="postgres")
        sql = "SELECT * FROM users LIMIT 10"

        is_valid, errors = validator.validate_sql(sql)

        assert is_valid is True
        assert len(errors) == 0

    def test_subquery_validation(self):
        """Test validation of queries with subqueries."""
        validator = SQLValidator()
        sql = """
        SELECT * FROM users
        WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)
        """

        is_valid, errors = validator.validate_sql(sql)

        assert is_valid is True
        assert len(errors) == 0

    def test_validation_error_formatting(self):
        """Test ValidationError formatting."""
        error1 = ValidationError("Syntax error")
        assert str(error1) == "Syntax error"

        error2 = ValidationError("Syntax error", line=10)
        assert "Line 10" in str(error2)

        error3 = ValidationError("Syntax error", line=10, column=5)
        assert "Line 10" in str(error3)
        assert "Column 5" in str(error3)
