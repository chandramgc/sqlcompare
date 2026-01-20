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
    ) AS hi_value_category_spend,
    SUM(
      CASE
        WHEN oi.unit_price >= 500 THEN
          CASE
            WHEN oi.quantity > 1 THEN oi.quantity * oi.unit_price * 1.1  -- bulk premium
            ELSE oi.quantity * oi.unit_price
          END
        WHEN oi.unit_price >= 100 THEN
          CASE
            WHEN oi.quantity >= 5 THEN oi.quantity * oi.unit_price * 0.95  -- volume discount
            WHEN oi.quantity >= 3 THEN oi.quantity * oi.unit_price * 0.98
            ELSE oi.quantity * oi.unit_price
          END
        WHEN oi.unit_price >= 20 THEN oi.quantity * oi.unit_price
        ELSE
          CASE
            WHEN oi.quantity > 10 THEN oi.quantity * oi.unit_price * 0.9  -- clearance bulk
            ELSE oi.quantity * oi.unit_price
          END
      END
    ) AS adjusted_value
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
    (COALESCE(pa.captured_amount, 0) - COALESCE(ra.total_refunds, 0)) AS net_paid_after_returns,
    CASE
      WHEN COALESCE(ra.return_count, 0) = 0 THEN 'no_returns'
      WHEN COALESCE(ra.return_count, 0) = 1 THEN
        CASE
          WHEN COALESCE(ra.total_refunds, 0) / NULLIF(COALESCE(pa.captured_amount, 0), 0) > 0.5 THEN 'high_value_single_return'
          ELSE 'low_value_single_return'
        END
      WHEN COALESCE(ra.return_count, 0) >= 2 THEN
        CASE
          WHEN COALESCE(ra.total_refunds, 0) > COALESCE(pa.captured_amount, 0) * 0.8 THEN 'serial_returner_high_refund'
          WHEN COALESCE(ra.return_count, 0) >= 3 THEN 'serial_returner_multiple'
          ELSE 'moderate_returner'
        END
      ELSE 'unknown_return_status'
    END AS return_risk_category,
    CASE
      WHEN ro.status = 'paid' THEN
        CASE
          WHEN pa.last_payment_method = 'credit_card' THEN 'cc_paid'
          WHEN pa.last_payment_method IN ('paypal', 'stripe') THEN 'digital_wallet_paid'
          ELSE 'other_payment_paid'
        END
      WHEN ro.status IN ('shipped', 'delivered') THEN
        CASE
          WHEN COALESCE(oia.hi_value_category_spend, 0) > COALESCE(oia.items_subtotal, 0) * 0.5 THEN 'hi_value_shipped'
          ELSE 'regular_shipped'
        END
      ELSE 'non_completed'
    END AS fulfillment_category
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
  ) AS most_recent_successful_order_id,
  CASE
    WHEN cs.segment = 'subscriber' THEN
      CASE
        WHEN SUM(oe.return_count) = 0 THEN 'loyal_subscriber_no_returns'
        WHEN SUM(oe.return_count) / NULLIF(COUNT(*), 0) > 0.3 THEN 'problematic_subscriber'
        ELSE 'regular_subscriber'
      END
    WHEN cs.segment = 'new' THEN
      CASE
        WHEN COUNT(*) = 1 THEN 'first_time_buyer'
        WHEN COUNT(*) >= 3 THEN 'rapid_repeat_buyer'
        ELSE 'exploring_new_customer'
      END
    ELSE
      CASE
        WHEN SUM(oe.net_paid_after_returns) >= 5000 THEN 'high_value_standard'
        WHEN AVG(NULLIF(oe.item_count, 0)) > 8 THEN 'bulk_standard_buyer'
        WHEN SUM(oe.return_count) / NULLIF(COUNT(*), 0) > 0.5 THEN 'return_prone_standard'
        ELSE 'regular_standard'
      END
  END AS detailed_customer_profile,
  CASE
    WHEN cs.region IN ('US-WEST', 'US-EAST') THEN
      CASE
        WHEN MAX(oe.hi_value_category_spend) > 1000 THEN 'us_premium'
        WHEN COUNT(*) > 10 THEN 'us_frequent'
        ELSE 'us_regular'
      END
    WHEN cs.region IN ('EU-NORTH', 'EU-SOUTH') THEN
      CASE
        WHEN SUM(oe.return_count) > 5 THEN 'eu_high_return'
        ELSE 'eu_standard'
      END
    WHEN cs.region = 'UNKNOWN' THEN 'region_unknown'
    ELSE
      CASE
        WHEN SUM(oe.net_paid_after_returns) / NULLIF(COUNT(*), 0) > 200 THEN 'other_high_aov'
        ELSE 'other_standard'
      END
  END AS regional_behavior_segment
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
  ) AS most_recent_successful_order_id,
  CASE
    WHEN cs.segment = 'subscriber' THEN
      CASE
        WHEN SUM(oe.return_count) = 0 THEN 'loyal_subscriber_no_returns'
        WHEN SUM(oe.return_count) / NULLIF(COUNT(*), 0) > 0.3 THEN 'problematic_subscriber'
        ELSE 'regular_subscriber'
      END
    WHEN cs.segment = 'new' THEN
      CASE
        WHEN COUNT(*) = 1 THEN 'first_time_buyer'
        WHEN COUNT(*) >= 3 THEN 'rapid_repeat_buyer'
        ELSE 'exploring_new_customer'
      END
    ELSE
      CASE
        WHEN SUM(oe.net_paid_after_returns) >= 5000 THEN 'high_value_standard'
        WHEN AVG(NULLIF(oe.item_count, 0)) > 8 THEN 'bulk_standard_buyer'
        WHEN SUM(oe.return_count) / NULLIF(COUNT(*), 0) > 0.5 THEN 'return_prone_standard'
        ELSE 'regular_standard'
      END
  END AS detailed_customer_profile,
  CASE
    WHEN cs.region IN ('US-WEST', 'US-EAST') THEN
      CASE
        WHEN MAX(oe.hi_value_category_spend) > 1000 THEN 'us_premium'
        WHEN COUNT(*) > 10 THEN 'us_frequent'
        ELSE 'us_regular'
      END
    WHEN cs.region IN ('EU-NORTH', 'EU-SOUTH') THEN
      CASE
        WHEN SUM(oe.return_count) > 5 THEN 'eu_high_return'
        ELSE 'eu_standard'
      END
    WHEN cs.region = 'UNKNOWN' THEN 'region_unknown'
    ELSE
      CASE
        WHEN SUM(oe.net_paid_after_returns) / NULLIF(COUNT(*), 0) > 200 THEN 'other_high_aov'
        ELSE 'other_standard'
      END
  END AS regional_behavior_segment
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
