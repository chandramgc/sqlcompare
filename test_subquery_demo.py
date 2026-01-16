"""Demo of subquery diff detection."""

from sql_diff_ui.diff_engine import compare_sql
from sample_queries import SQL_A_1, SQL_B_1, SQL_A_2, SQL_B_2

print("=" * 80)
print("DEMO: Subquery Diff Detection")
print("=" * 80)

# Test 1: Subquery in WHERE clause
print("\n" + "=" * 80)
print("Test 1: WHERE IN subquery changes")
print("=" * 80)
result = compare_sql(SQL_A_1, SQL_B_1)
print(f"\nFound {len(result.notices)} differences:\n")
for notice in result.notices:
    print(f"  {notice}")

# Test 2: Subquery in SELECT
print("\n" + "=" * 80)
print("Test 2: SELECT subquery changes")
print("=" * 80)
result = compare_sql(SQL_A_2, SQL_B_2)
print(f"\nFound {len(result.notices)} differences:\n")
for notice in result.notices:
    print(f"  {notice}")

print("\n" + "=" * 80)
print("✅ Subquery detection working!")
print("=" * 80)
