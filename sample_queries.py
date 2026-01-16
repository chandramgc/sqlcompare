"""Sample SQL queries with subqueries for testing the diff tool."""

# Sample 1: Subquery in WHERE clause
SQL_A_1 = """
SELECT 
    u.id,
    u.name,
    u.email,
    u.total_orders
FROM users u
WHERE u.id IN (
    SELECT user_id 
    FROM orders 
    WHERE status = 'completed' 
    AND created_at >= '2024-01-01'
)
ORDER BY u.total_orders DESC
LIMIT 100
"""

SQL_B_1 = """
SELECT 
    u.id,
    u.name,
    u.email,
    u.total_orders,
    u.last_login
FROM users u
WHERE u.id IN (
    SELECT user_id 
    FROM orders 
    WHERE status IN ('completed', 'shipped')
    AND created_at >= '2024-01-01'
    AND total_amount > 100
)
ORDER BY u.total_orders DESC, u.last_login DESC
LIMIT 50
"""

# Sample 2: Subquery in SELECT (derived column)
SQL_A_2 = """
SELECT 
    p.id,
    p.product_name,
    p.category,
    p.price,
    (SELECT COUNT(*) FROM order_items oi WHERE oi.product_id = p.id) as order_count
FROM products p
WHERE p.active = true
AND p.category IN ('Electronics', 'Books')
"""

SQL_B_2 = """
SELECT 
    p.id,
    p.product_name,
    p.category,
    p.price,
    p.stock_quantity,
    (SELECT COUNT(*) FROM order_items oi WHERE oi.product_id = p.id AND oi.created_at >= '2024-01-01') as order_count,
    (SELECT AVG(rating) FROM reviews r WHERE r.product_id = p.id) as avg_rating
FROM products p
WHERE p.active = true
AND p.category IN ('Electronics', 'Books', 'Toys')
AND p.stock_quantity > 0
"""

# Sample 3: Subquery in FROM (derived table)
SQL_A_3 = """
SELECT 
    dept_name,
    avg_salary,
    employee_count
FROM (
    SELECT 
        d.name as dept_name,
        AVG(e.salary) as avg_salary,
        COUNT(e.id) as employee_count
    FROM departments d
    LEFT JOIN employees e ON d.id = e.department_id
    WHERE e.status = 'active'
    GROUP BY d.name
) dept_stats
WHERE avg_salary > 50000
ORDER BY avg_salary DESC
"""

SQL_B_3 = """
SELECT 
    dept_name,
    avg_salary,
    employee_count,
    total_salary
FROM (
    SELECT 
        d.name as dept_name,
        AVG(e.salary) as avg_salary,
        COUNT(e.id) as employee_count,
        SUM(e.salary) as total_salary
    FROM departments d
    INNER JOIN employees e ON d.id = e.department_id
    WHERE e.status = 'active'
    AND e.hire_date >= '2020-01-01'
    GROUP BY d.name
    HAVING COUNT(e.id) >= 5
) dept_stats
WHERE avg_salary > 60000
ORDER BY avg_salary DESC, employee_count DESC
"""

# Sample 4: Correlated subquery with EXISTS
SQL_A_4 = """
SELECT 
    c.id,
    c.customer_name,
    c.email,
    c.country
FROM customers c
WHERE EXISTS (
    SELECT 1 
    FROM orders o 
    WHERE o.customer_id = c.id 
    AND o.status = 'completed'
)
"""

SQL_B_4 = """
SELECT 
    c.id,
    c.customer_name,
    c.email,
    c.country,
    c.vip_status
FROM customers c
WHERE EXISTS (
    SELECT 1 
    FROM orders o 
    WHERE o.customer_id = c.id 
    AND o.status IN ('completed', 'shipped')
    AND o.total_amount > 1000
)
AND c.country IN ('USA', 'Canada', 'UK')
"""


if __name__ == "__main__":
    print("=" * 80)
    print("SAMPLE 1: Subquery in WHERE - IN clause")
    print("=" * 80)
    print("\nSQL A:")
    print(SQL_A_1)
    print("\nSQL B:")
    print(SQL_B_1)
    print("\nKey Differences:")
    print("- Added 'last_login' column")
    print("- Changed status filter from single to multiple values")
    print("- Added total_amount filter in subquery")
    print("- Added second ORDER BY column")
    print("- Changed LIMIT from 100 to 50")
    
    print("\n" + "=" * 80)
    print("SAMPLE 2: Subquery in SELECT - Derived columns")
    print("=" * 80)
    print("\nSQL A:")
    print(SQL_A_2)
    print("\nSQL B:")
    print(SQL_B_2)
    print("\nKey Differences:")
    print("- Added 'stock_quantity' column")
    print("- Modified order_count subquery with date filter")
    print("- Added new avg_rating subquery")
    print("- Added 'Toys' to category filter")
    print("- Added stock_quantity > 0 condition")
    
    print("\n" + "=" * 80)
    print("SAMPLE 3: Subquery in FROM - Derived table")
    print("=" * 80)
    print("\nSQL A:")
    print(SQL_A_3)
    print("\nSQL B:")
    print(SQL_B_3)
    print("\nKey Differences:")
    print("- Added 'total_salary' column in subquery")
    print("- Changed LEFT JOIN to INNER JOIN")
    print("- Added hire_date filter")
    print("- Added HAVING clause")
    print("- Changed avg_salary threshold from 50000 to 60000")
    print("- Added second ORDER BY column")
    
    print("\n" + "=" * 80)
    print("SAMPLE 4: Correlated subquery with EXISTS")
    print("=" * 80)
    print("\nSQL A:")
    print(SQL_A_4)
    print("\nSQL B:")
    print(SQL_B_4)
    print("\nKey Differences:")
    print("- Added 'vip_status' column")
    print("- Changed status from single to multiple values in EXISTS")
    print("- Added total_amount filter in EXISTS subquery")
    print("- Added country filter in outer WHERE")
