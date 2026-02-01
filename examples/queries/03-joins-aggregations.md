# Complex Queries with Joins and Aggregations

Examples of more complex analytical queries using joins and aggregations.

## Simple Join

```
Run this query:
SELECT 
    c.name as customer_name,
    o.orderkey,
    o.totalprice
FROM tpch.tiny.customer c
JOIN tpch.tiny.orders o ON c.custkey = o.custkey
LIMIT 20
```

## Multiple Joins

```
Run this query:
SELECT 
    c.name as customer_name,
    o.orderkey,
    l.linenumber,
    l.quantity,
    l.extendedprice
FROM tpch.tiny.customer c
JOIN tpch.tiny.orders o ON c.custkey = o.custkey
JOIN tpch.tiny.lineitem l ON o.orderkey = l.orderkey
LIMIT 50
```

## Aggregations with Joins

```
Run this query:
SELECT 
    c.name as customer_name,
    COUNT(DISTINCT o.orderkey) as order_count,
    SUM(l.extendedprice) as total_spent
FROM tpch.tiny.customer c
JOIN tpch.tiny.orders o ON c.custkey = o.custkey
JOIN tpch.tiny.lineitem l ON o.orderkey = l.orderkey
GROUP BY c.name
ORDER BY total_spent DESC
LIMIT 10
```

## Window Functions

```
Run this query:
SELECT 
    name,
    acctbal,
    ROW_NUMBER() OVER (ORDER BY acctbal DESC) as rank,
    AVG(acctbal) OVER () as avg_balance
FROM tpch.tiny.customer
LIMIT 20
```

## CTEs (Common Table Expressions)

```
Run this query:
WITH customer_orders AS (
    SELECT 
        c.custkey,
        c.name,
        COUNT(o.orderkey) as order_count
    FROM tpch.tiny.customer c
    LEFT JOIN tpch.tiny.orders o ON c.custkey = o.custkey
    GROUP BY c.custkey, c.name
)
SELECT 
    name,
    order_count,
    CASE 
        WHEN order_count = 0 THEN 'No orders'
        WHEN order_count < 5 THEN 'Few orders'
        ELSE 'Many orders'
    END as order_category
FROM customer_orders
ORDER BY order_count DESC
LIMIT 20
```
