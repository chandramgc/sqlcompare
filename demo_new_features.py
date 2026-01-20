"""Demo for new features: Line number toggle and CASE statement validation."""

from sql_diff_ui.sql_validator import SQLValidator


def demo_case_validation():
    """Demo CASE statement validation."""
    print("=" * 70)
    print("DEMO: CASE Statement Validation")
    print("=" * 70)
    
    validator = SQLValidator()
    
    # Test 1: CASE without END
    print("\n1. CASE without END:")
    print("-" * 70)
    sql1 = """
    SELECT 
        id,
        CASE
            WHEN status = 'active' THEN 'Active'
            WHEN status = 'inactive' THEN 'Inactive'
    FROM users
    """
    is_valid, errors = validator.validate_sql(sql1)
    print(f"SQL:\n{sql1}")
    print(f"\nValid: {is_valid}")
    for error in errors:
        if hasattr(error, 'line') and error.line:
            print(f"  ❌ Line {error.line}: {error.message}")
        else:
            print(f"  ❌ {error.message}")
    
    # Test 2: WHEN without THEN
    print("\n\n2. WHEN without THEN:")
    print("-" * 70)
    sql2 = """
    SELECT 
        id,
        CASE
            WHEN status = 'active'
            ELSE 'Unknown'
        END
    FROM users
    """
    is_valid, errors = validator.validate_sql(sql2)
    print(f"SQL:\n{sql2}")
    print(f"\nValid: {is_valid}")
    for error in errors:
        if hasattr(error, 'line') and error.line:
            print(f"  ❌ Line {error.line}: {error.message}")
        else:
            print(f"  ❌ {error.message}")
    
    # Test 3: Valid CASE statement
    print("\n\n3. Valid CASE statement:")
    print("-" * 70)
    sql3 = """
    SELECT 
        id,
        CASE
            WHEN status = 'active' THEN 'Active'
            WHEN status = 'inactive' THEN 'Inactive'
            ELSE 'Unknown'
        END as status_text
    FROM users
    """
    is_valid, errors = validator.validate_sql(sql3)
    print(f"SQL:\n{sql3}")
    print(f"\nValid: {is_valid}")
    if is_valid:
        print("  ✅ SQL is valid!")
    else:
        for error in errors:
            if hasattr(error, 'line') and error.line:
                print(f"  ❌ Line {error.line}: {error.message}")
            else:
                print(f"  ❌ {error.message}")
    
    # Test 4: Complex CASE with multiple conditions
    print("\n\n4. Complex CASE statement:")
    print("-" * 70)
    sql4 = """
    SELECT 
        id,
        name,
        CASE
            WHEN age < 18 THEN 'Minor'
            WHEN age >= 18 AND age < 65 THEN 'Adult'
            WHEN age >= 65 THEN 'Senior'
            ELSE 'Unknown'
        END as age_group,
        CASE status
            WHEN 'A' THEN 'Active'
            WHEN 'I' THEN 'Inactive'
            ELSE 'Pending'
        END as status_text
    FROM users
    WHERE active = true
    """
    is_valid, errors = validator.validate_sql(sql4)
    print(f"SQL:\n{sql4}")
    print(f"\nValid: {is_valid}")
    if is_valid:
        print("  ✅ SQL is valid!")
    else:
        for error in errors:
            if hasattr(error, 'line') and error.line:
                print(f"  ❌ Line {error.line}: {error.message}")
            else:
                print(f"  ❌ {error.message}")


def demo_ui_toggle():
    """Demo information about the UI toggle feature."""
    print("\n\n" + "=" * 70)
    print("NEW FEATURE: Line Number Toggle in UI")
    print("=" * 70)
    print("\nThe Streamlit UI now includes a 'Show line numbers' checkbox in the")
    print("comparison options section.")
    print("\n✅ Benefits:")
    print("  • Toggle line numbers on/off in error SQL views")
    print("  • Reduces visual clutter when not needed")
    print("  • Enabled by default for quick debugging")
    print("  • Works independently for SQL A and SQL B validation errors")
    print("\n📝 Usage:")
    print("  1. Run the app: make run")
    print("  2. Look for 'Show line numbers' checkbox in options")
    print("  3. Uncheck to hide numbered SQL views")
    print("  4. Check to show detailed line-by-line SQL display")
    print("\nWhen enabled, validation errors will show an expandable section")
    print("with line-numbered SQL for easy navigation to error locations.")


if __name__ == "__main__":
    demo_case_validation()
    demo_ui_toggle()
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
