"""Demo script for SQL validation and beautification."""

from sql_diff_ui.sql_validator import SQLValidator


def print_separator():
    """Print a separator line."""
    print("=" * 80)


def demo_valid_sql():
    """Demonstrate validation of valid SQL."""
    print("\n🟢 DEMO 1: Valid SQL Query")
    print_separator()

    sql = """
    select id,name,email from users 
    where status='active' and role='admin'
    order by created_at desc
    """

    validator = SQLValidator()
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL:\n{sql}")
    print(f"\nValid: {is_valid}")

    if is_valid:
        print(f"\n✨ Beautified SQL:\n{beautified}")
    else:
        print(f"\nErrors: {[str(e) for e in errors]}")


def demo_invalid_syntax():
    """Demonstrate validation of SQL with syntax errors."""
    print("\n\n🔴 DEMO 2: Invalid SQL Syntax")
    print_separator()

    sql = "SELECT * FORM users WHERE status = 'active'"

    validator = SQLValidator()
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL:\n{sql}")
    print(f"\nValid: {is_valid}")

    if not is_valid:
        print(f"\n❌ Validation Errors:")
        for error in errors:
            print(f"  • {error}")


def demo_unbalanced_parentheses():
    """Demonstrate detection of unbalanced parentheses."""
    print("\n\n🔴 DEMO 3: Unbalanced Parentheses")
    print_separator()

    sql = "SELECT * FROM users WHERE (status = 'active' AND role = 'admin'"

    validator = SQLValidator()
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL:\n{sql}")
    print(f"\nValid: {is_valid}")

    if not is_valid:
        print(f"\n❌ Validation Errors:")
        for error in errors:
            print(f"  • {error}")


def demo_unbalanced_quotes():
    """Demonstrate detection of unbalanced quotes."""
    print("\n\n🔴 DEMO 4: Unbalanced Quotes")
    print_separator()

    sql = "SELECT * FROM users WHERE name = 'John"

    validator = SQLValidator()
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL:\n{sql}")
    print(f"\nValid: {is_valid}")

    if not is_valid:
        print(f"\n❌ Validation Errors:")
        for error in errors:
            print(f"  • {error}")


def demo_empty_sql():
    """Demonstrate validation of empty SQL."""
    print("\n\n🔴 DEMO 5: Empty SQL Query")
    print_separator()

    sql = ""

    validator = SQLValidator()
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL: '{sql}'")
    print(f"\nValid: {is_valid}")

    if not is_valid:
        print(f"\n❌ Validation Errors:")
        for error in errors:
            print(f"  • {error}")


def demo_complex_query():
    """Demonstrate validation and beautification of complex query."""
    print("\n\n🟢 DEMO 6: Complex Query with Joins and Subqueries")
    print_separator()

    sql = """
    SELECT u.id,u.name,COUNT(o.id) as order_count FROM users u 
    LEFT JOIN orders o ON u.id=o.user_id 
    WHERE u.status='active' AND u.id IN (SELECT user_id FROM premium_users) 
    GROUP BY u.id,u.name HAVING COUNT(o.id)>5 ORDER BY order_count DESC LIMIT 10
    """

    validator = SQLValidator()
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL (compact):\n{sql}")
    print(f"\nValid: {is_valid}")

    if is_valid:
        print(f"\n✨ Beautified SQL:\n{beautified}")


def demo_dialect_specific():
    """Demonstrate dialect-specific validation."""
    print("\n\n🟢 DEMO 7: PostgreSQL-specific Query")
    print_separator()

    sql = """
    SELECT * FROM users 
    WHERE created_at > NOW() - INTERVAL '7 days'
    LIMIT 10
    """

    validator = SQLValidator(dialect="postgres")
    is_valid, beautified, errors = validator.validate_and_beautify(sql)

    print(f"Original SQL:\n{sql}")
    print(f"\nValid: {is_valid} (PostgreSQL dialect)")

    if is_valid:
        print(f"\n✨ Beautified SQL:\n{beautified}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print(" " * 20 + "SQL VALIDATOR & BEAUTIFIER DEMO")
    print("=" * 80)

    demo_valid_sql()
    demo_invalid_syntax()
    demo_unbalanced_parentheses()
    demo_unbalanced_quotes()
    demo_empty_sql()
    demo_complex_query()
    demo_dialect_specific()

    print("\n" + "=" * 80)
    print(" " * 30 + "DEMO COMPLETE")
    print("=" * 80 + "\n")
