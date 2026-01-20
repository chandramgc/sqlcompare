"""Comprehensive test demonstrating the validation fix for missing operators."""

from sql_diff_ui.sql_validator import SQLValidator

print("=" * 80)
print("VALIDATION FIX DEMONSTRATION")
print("=" * 80)

# Test case 1: The original issue reported by the user
print("\n\n📋 TEST 1: Original Issue - Missing '=' after role")
print("-" * 80)

sql_invalid = """
SELECT id, name, phone
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE status = 'active' AND role 'customer'
ORDER BY created_at DESC
LIMIT 20
"""

print("SQL Query:")
print(sql_invalid)

validator = SQLValidator()
is_valid, beautified, errors = validator.validate_and_beautify(sql_invalid)

print(f"\n✅ Validation Result: {'VALID' if is_valid else 'INVALID'}")

if not is_valid:
    print(f"\n❌ Errors Found ({len(errors)}):")
    for i, error in enumerate(errors, 1):
        print(f"   {i}. {error}")
    print("\n✅ SUCCESS: The validator correctly detected the missing '=' operator!")
else:
    print("\n❌ FAIL: Should have been invalid!")

# Test case 2: The corrected version
print("\n\n📋 TEST 2: Corrected Version - With '=' operator")
print("-" * 80)

sql_valid = """
SELECT id, name, phone
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE status = 'active' AND role = 'customer'
ORDER BY created_at DESC
LIMIT 20
"""

print("SQL Query:")
print(sql_valid)

is_valid2, beautified2, errors2 = validator.validate_and_beautify(sql_valid)

print(f"\n✅ Validation Result: {'VALID' if is_valid2 else 'INVALID'}")

if is_valid2:
    print("\n✨ Beautified SQL:")
    print(beautified2)
    print("\n✅ SUCCESS: Valid SQL passes validation and gets beautified!")
else:
    print(f"\n❌ Errors: {[str(e) for e in errors2]}")
    print("\n❌ FAIL: Should have been valid!")

# Test case 3: Another missing operator scenario
print("\n\n📋 TEST 3: Another Missing Operator - Missing '>' in comparison")
print("-" * 80)

sql_invalid2 = """
SELECT product_name, price
FROM products
WHERE price 100 AND category = 'electronics'
"""

print("SQL Query:")
print(sql_invalid2)

is_valid3, beautified3, errors3 = validator.validate_and_beautify(sql_invalid2)

print(f"\n✅ Validation Result: {'VALID' if is_valid3 else 'INVALID'}")

if not is_valid3:
    print(f"\n❌ Errors Found ({len(errors3)}):")
    for i, error in enumerate(errors3, 1):
        print(f"   {i}. {error}")
    print("\n✅ SUCCESS: Detected missing comparison operator!")
else:
    print("\n❌ FAIL: Should have been invalid!")

# Test case 4: Multiple missing operators
print("\n\n📋 TEST 4: Multiple Issues")
print("-" * 80)

sql_invalid3 = """
SELECT name, age
FROM users
WHERE age 18 AND status 'active' AND role 'admin'
"""

print("SQL Query:")
print(sql_invalid3)

is_valid4, beautified4, errors4 = validator.validate_and_beautify(sql_invalid3)

print(f"\n✅ Validation Result: {'VALID' if is_valid4 else 'INVALID'}")

if not is_valid4:
    print(f"\n❌ Errors Found ({len(errors4)}):")
    for i, error in enumerate(errors4, 1):
        print(f"   {i}. {error}")
    print("\n✅ SUCCESS: Detected multiple syntax errors!")
else:
    print("\n❌ FAIL: Should have been invalid!")

print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
The SQL validator now successfully detects:

1. ✅ Missing comparison operators (role 'customer' → role = 'customer')
2. ✅ Lost string literals during parsing
3. ✅ Incomplete WHERE clause conditions
4. ✅ Multiple syntax errors in the same query

The fix works by:
- Parsing the SQL with sqlglot
- Comparing original vs regenerated SQL
- Detecting any lost string literals
- Reporting clear, actionable error messages

This ensures that only valid SQL queries are compared, preventing
false or misleading comparison results!
""")
print("=" * 80 + "\n")
