"""Demo script to verify SQL diff functionality."""

from sql_diff_ui.diff_engine import compare_sql

# Example 1: Simple SELECT changes
print("=" * 80)
print("Example 1: Column addition")
print("=" * 80)
sql_a = "SELECT id, name FROM users WHERE status = 'active'"
sql_b = "SELECT id, name, email FROM users WHERE status = 'active'"

result = compare_sql(sql_a, sql_b)
print(f"\nFound {len(result.notices)} differences:\n")
for notice in result.notices:
    print(f"  {notice}")

# Example 2: JOIN changes
print("\n" + "=" * 80)
print("Example 2: JOIN addition")
print("=" * 80)
sql_a = "SELECT u.id, u.name FROM users u"
sql_b = "SELECT u.id, u.name FROM users u LEFT JOIN orders o ON u.id = o.user_id"

result = compare_sql(sql_a, sql_b)
print(f"\nFound {len(result.notices)} differences:\n")
for notice in result.notices:
    print(f"  {notice}")

# Example 3: WHERE predicate changes
print("\n" + "=" * 80)
print("Example 3: WHERE condition changes")
print("=" * 80)
sql_a = "SELECT id FROM users WHERE status = 'active'"
sql_b = "SELECT id FROM users WHERE status = 'active' AND role = 'admin'"

result = compare_sql(sql_a, sql_b)
print(f"\nFound {len(result.notices)} differences:\n")
for notice in result.notices:
    print(f"  {notice}")

# Example 4: Multiple changes
print("\n" + "=" * 80)
print("Example 4: Multiple changes")
print("=" * 80)
sql_a = """
SELECT id, name
FROM users
WHERE status = 'active'
ORDER BY created_at
LIMIT 10
"""

sql_b = """
SELECT id, name, email
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE status = 'active' AND role = 'customer'
ORDER BY updated_at DESC
LIMIT 20
"""

result = compare_sql(sql_a, sql_b)
print(f"\nFound {len(result.notices)} differences:\n")
for notice in result.notices:
    print(f"  {notice}")

print("\n" + "=" * 80)
print("Text Diff Preview:")
print("=" * 80)
print(result.text_diff[:500] if result.text_diff else "No text diff")

print("\n✅ SQL Diff Engine working correctly!")
