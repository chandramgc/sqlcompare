-- Sample Complex Query A: Customer Order Analytics with CTEs, Subqueries, UNION
-- Features: CTEs, window functions, correlated subqueries, aggregations, UNION ALL

WITH recent_orders AS (
  SELECT
    o.id AS order_id,
    o.customer_id,
    o.status,
    o.created_at,
    o.currency,
    o.total_amount,
    o.promo_code
  FROM orders o
  WHERE o.created_at >= CURRENT_DATE - INTERVAL '90 days'
),
order_items_agg AS (
  SELECT
    oi.order_id,
    COUNT(*) AS item_count,
    SUM(oi.quantity) AS units,
    SUM(oi.quantity * oi.unit_price) AS items_subtotal,
    MAX(oi.unit_price) AS max_unit_price
  FROM order_items oi
  GROUP BY oi.order_id
),
payments_agg AS (
  SELECT
    p.order_id,
    SUM(CASE WHEN p.status = 'captured' THEN p.amount ELSE 0 END) AS captured_amount,
    SUM(CASE WHEN p.status = 'refunded' THEN p.amount ELSE 0 END) AS refunded_amount,
    MAX(p.captured_at) AS last_captured_at
  FROM payments p
  GROUP BY p.order_id
),
order_enriched AS (
  SELECT
    ro.order_id,
    ro.customer_id,
    ro.status,
    ro.created_at,
    ro.currency,
    ro.total_amount,
    COALESCE(oia.item_count, 0) AS item_count,
    COALESCE(oia.units, 0) AS units,
    COALESCE(oia.items_subtotal, 0) AS items_subtotal,
    COALESCE(pa.captured_amount, 0) AS captured_amount,
    COALESCE(pa.refunded_amount, 0) AS refunded_amount,
    (COALESCE(pa.captured_amount, 0) - COALESCE(pa.refunded_amount, 0)) AS net_paid_amount,
    ro.promo_code,
    CASE
      WHEN ro.promo_code IS NULL THEN 'no_promo'
      WHEN ro.promo_code ILIKE 'VIP%' THEN 'vip_promo'
      ELSE 'other_promo'
    END AS promo_bucket
  FROM recent_orders ro
  LEFT JOIN order_items_agg oia ON oia.order_id = ro.order_id
  LEFT JOIN payments_agg pa ON pa.order_id = ro.order_id
),
customer_latest_region AS (
  SELECT
    a.customer_id,
    a.region,
    ROW_NUMBER() OVER (PARTITION BY a.customer_id ORDER BY a.updated_at DESC) AS rn
  FROM addresses a
),
customer_base AS (
  SELECT
    c.id AS customer_id,
    c.email,
    c.created_at AS customer_created_at,
    COALESCE(clr.region, 'UNKNOWN') AS region,
    (
      SELECT COUNT(*)
      FROM support_tickets t
      WHERE t.customer_id = c.id
        AND t.created_at >= CURRENT_DATE - INTERVAL '180 days'
    ) AS tickets_last_180d,
    EXISTS (
      SELECT 1
      FROM subscriptions s
      WHERE s.customer_id = c.id
        AND s.status = 'active'
    ) AS has_active_subscription
  FROM customers c
  LEFT JOIN customer_latest_region clr
    ON clr.customer_id = c.id AND clr.rn = 1
)
SELECT
  cb.customer_id,
  cb.email,
  cb.region,
  cb.customer_created_at,
  cb.tickets_last_180d,
  cb.has_active_subscription,
  oe.currency,
  COUNT(*) FILTER (WHERE oe.status IN ('paid','shipped','delivered')) AS successful_orders,
  COUNT(*) FILTER (WHERE oe.status IN ('cancelled','failed')) AS failed_orders,
  SUM(oe.net_paid_amount) AS net_revenue,
  AVG(NULLIF(oe.item_count, 0)) AS avg_item_count,
  MAX(oe.created_at) AS last_order_at,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY oe.net_paid_amount) AS median_order_net_paid,
  (
    SELECT oe2.order_id
    FROM order_enriched oe2
    WHERE oe2.customer_id = cb.customer_id
    ORDER BY oe2.net_paid_amount DESC, oe2.created_at DESC
    LIMIT 1
  ) AS top_order_id
FROM customer_base cb
JOIN order_enriched oe
  ON oe.customer_id = cb.customer_id
WHERE cb.customer_created_at >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY
  cb.customer_id, cb.email, cb.region, cb.customer_created_at,
  cb.tickets_last_180d, cb.has_active_subscription, oe.currency

UNION ALL

SELECT
  cb.customer_id,
  cb.email,
  cb.region,
  cb.customer_created_at,
  cb.tickets_last_180d,
  cb.has_active_subscription,
  'ALL' AS currency,
  COUNT(*) FILTER (WHERE oe.status IN ('paid','shipped','delivered')) AS successful_orders,
  COUNT(*) FILTER (WHERE oe.status IN ('cancelled','failed')) AS failed_orders,
  SUM(oe.net_paid_amount) AS net_revenue,
  AVG(NULLIF(oe.item_count, 0)) AS avg_item_count,
  MAX(oe.created_at) AS last_order_at,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY oe.net_paid_amount) AS median_order_net_paid,
  (
    SELECT oe2.order_id
    FROM order_enriched oe2
    WHERE oe2.customer_id = cb.customer_id
    ORDER BY oe2.net_paid_amount DESC, oe2.created_at DESC
    LIMIT 1
  ) AS top_order_id
FROM customer_base cb
JOIN order_enriched oe
  ON oe.customer_id = cb.customer_id
WHERE cb.customer_created_at >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY
  cb.customer_id, cb.email, cb.region, cb.customer_created_at,
  cb.tickets_last_180d, cb.has_active_subscription
ORDER BY net_revenue DESC, successful_orders DESC
LIMIT 200;
