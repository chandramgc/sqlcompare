-- Sample Complex Query B: Customer Returns & Inventory Risk Analysis
-- Features: CTEs, nested subqueries in WHERE/CASE, window functions, multiple joins, UNION ALL

WITH recent_orders AS (
  SELECT
    o.id AS order_id,
    o.customer_id,
    o.status,
    o.created_at,
    o.currency,
    o.total_amount,
    o.store_id
  FROM orders o
  WHERE o.created_at >= CURRENT_DATE - INTERVAL '120 days'
    AND o.store_id IN (
      SELECT s.id
      FROM stores s
      WHERE s.is_active = TRUE
    )
),
order_items_agg AS (
  SELECT
    oi.order_id,
    COUNT(*) AS item_count,
    SUM(oi.quantity) AS units,
    SUM(oi.quantity * oi.unit_price) AS items_subtotal,
    SUM(
      CASE
        WHEN oi.product_id IN (
          SELECT p.id
          FROM products p
          WHERE p.category IN ('electronics', 'appliances')
        )
        THEN oi.quantity * oi.unit_price
        ELSE 0
      END
    ) AS hi_value_category_spend
  FROM order_items oi
  GROUP BY oi.order_id
),
payments_agg AS (
  SELECT
    p.order_id,
    SUM(CASE WHEN p.status = 'captured' THEN p.amount ELSE 0 END) AS captured_amount,
    MAX(p.payment_method) FILTER (WHERE p.status = 'captured') AS last_payment_method
  FROM payments p
  GROUP BY p.order_id
),
returns_agg AS (
  SELECT
    r.order_id,
    COUNT(*) AS return_count,
    SUM(r.refund_amount) AS total_refunds,
    MAX(r.created_at) AS last_return_at
  FROM returns r
  WHERE r.created_at >= CURRENT_DATE - INTERVAL '180 days'
  GROUP BY r.order_id
),
inventory_risk AS (
  SELECT
    i.product_id,
    CASE
      WHEN i.on_hand_qty <= i.reorder_point THEN 'low_stock'
      WHEN i.on_hand_qty <= i.reorder_point * 2 THEN 'watch'
      ELSE 'ok'
    END AS stock_risk
  FROM inventory i
),
order_enriched AS (
  SELECT
    ro.order_id,
    ro.customer_id,
    ro.status,
    ro.created_at,
    ro.currency,
    ro.total_amount,
    ro.store_id,
    COALESCE(oia.item_count, 0) AS item_count,
    COALESCE(oia.units, 0) AS units,
    COALESCE(oia.items_subtotal, 0) AS items_subtotal,
    COALESCE(oia.hi_value_category_spend, 0) AS hi_value_category_spend,
    COALESCE(pa.captured_amount, 0) AS captured_amount,
    pa.last_payment_method,
    COALESCE(ra.return_count, 0) AS return_count,
    COALESCE(ra.total_refunds, 0) AS total_refunds,
    (COALESCE(pa.captured_amount, 0) - COALESCE(ra.total_refunds, 0)) AS net_paid_after_returns
  FROM recent_orders ro
  LEFT JOIN order_items_agg oia ON oia.order_id = ro.order_id
  LEFT JOIN payments_agg pa ON pa.order_id = ro.order_id
  LEFT JOIN returns_agg ra ON ra.order_id = ro.order_id
),
customer_region AS (
  SELECT
    a.customer_id,
    a.region,
    ROW_NUMBER() OVER (PARTITION BY a.customer_id ORDER BY a.updated_at DESC) AS rn
  FROM addresses a
),
customer_segments AS (
  SELECT
    c.id AS customer_id,
    COALESCE(cr.region, 'UNKNOWN') AS region,
    CASE
      WHEN EXISTS (
        SELECT 1
        FROM subscriptions s
        WHERE s.customer_id = c.id AND s.status = 'active'
      ) THEN 'subscriber'
      WHEN c.created_at >= CURRENT_DATE - INTERVAL '90 days' THEN 'new'
      ELSE 'standard'
    END AS segment
  FROM customers c
  LEFT JOIN customer_region cr
    ON cr.customer_id = c.id AND cr.rn = 1
),
product_low_stock_orders AS (
  SELECT DISTINCT
    oe.customer_id,
    oe.order_id
  FROM order_enriched oe
  JOIN order_items oi ON oi.order_id = oe.order_id
  JOIN inventory_risk ir ON ir.product_id = oi.product_id
  WHERE ir.stock_risk IN ('low_stock', 'watch')
)
SELECT
  cs.customer_id,
  cs.region,
  cs.segment,
  oe.currency,
  COUNT(*) AS orders_count,
  SUM(oe.net_paid_after_returns) AS net_revenue_after_returns,
  SUM(oe.return_count) AS total_returns,
  AVG(NULLIF(oe.item_count, 0)) AS avg_items_per_order,
  MAX(oe.created_at) AS last_order_at,
  MAX(oe.hi_value_category_spend) AS max_hi_value_category_spend,
  SUM(CASE WHEN plo.order_id IS NOT NULL THEN 1 ELSE 0 END) AS orders_with_low_stock_items,
  (
    SELECT oe2.order_id
    FROM order_enriched oe2
    WHERE oe2.customer_id = cs.customer_id
      AND oe2.status IN ('paid','shipped','delivered')
    ORDER BY oe2.created_at DESC
    LIMIT 1
  ) AS most_recent_successful_order_id
FROM customer_segments cs
JOIN order_enriched oe
  ON oe.customer_id = cs.customer_id
LEFT JOIN product_low_stock_orders plo
  ON plo.customer_id = cs.customer_id AND plo.order_id = oe.order_id
WHERE oe.status NOT IN ('failed')
GROUP BY
  cs.customer_id, cs.region, cs.segment, oe.currency

UNION ALL

SELECT
  cs.customer_id,
  cs.region,
  cs.segment,
  'ALL' AS currency,
  COUNT(*) AS orders_count,
  SUM(oe.net_paid_after_returns) AS net_revenue_after_returns,
  SUM(oe.return_count) AS total_returns,
  AVG(NULLIF(oe.item_count, 0)) AS avg_items_per_order,
  MAX(oe.created_at) AS last_order_at,
  MAX(oe.hi_value_category_spend) AS max_hi_value_category_spend,
  SUM(CASE WHEN plo.order_id IS NOT NULL THEN 1 ELSE 0 END) AS orders_with_low_stock_items,
  (
    SELECT oe2.order_id
    FROM order_enriched oe2
    WHERE oe2.customer_id = cs.customer_id
      AND oe2.status IN ('paid','shipped','delivered')
    ORDER BY oe2.created_at DESC
    LIMIT 1
  ) AS most_recent_successful_order_id
FROM customer_segments cs
JOIN order_enriched oe
  ON oe.customer_id = cs.customer_id
LEFT JOIN product_low_stock_orders plo
  ON plo.customer_id = cs.customer_id AND plo.order_id = oe.order_id
WHERE oe.status NOT IN ('failed')
GROUP BY
  cs.customer_id, cs.region, cs.segment
ORDER BY net_revenue_after_returns DESC
LIMIT 200;
