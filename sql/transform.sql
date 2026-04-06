DROP TABLE IF EXISTS analytics.monthly_sales_summary;

CREATE TABLE analytics.monthly_sales_summary AS
SELECT
    DATE_TRUNC('month', oi.created_at)::date          AS year_month,
    p.product_name,
    SUM(oi.price_usd)                                 AS revenue,
    COUNT(DISTINCT oi.order_id)                       AS order_count,
    ROUND(
        (SUM(oi.price_usd) / COUNT(DISTINCT oi.order_id))::numeric,
        2
    )                                                 AS avg_order_value
FROM raw.order_items oi
JOIN raw.products p ON oi.product_id = p.product_id
GROUP BY 1, 2
ORDER BY 1, 2;
