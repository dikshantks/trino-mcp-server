# Basic Analytical Queries

Examples of common analytical queries you can run through the MCP server.

## Counting Records

```
Run this query: SELECT COUNT(*) FROM tpch.tiny.customer
```

## Aggregations

```
Run this query: 
SELECT 
    orderstatus,
    COUNT(*) as order_count,
    SUM(totalprice) as total_revenue
FROM tpch.tiny.orders
GROUP BY orderstatus
ORDER BY total_revenue DESC
```

## Filtering and Sorting

```
Run this query:
SELECT 
    custkey,
    name,
    acctbal
FROM tpch.tiny.customer
WHERE acctbal > 0
ORDER BY acctbal DESC
LIMIT 10
```

## Date Analysis

```
Run this query:
SELECT 
    DATE_TRUNC('month', orderdate) as month,
    COUNT(*) as orders,
    AVG(totalprice) as avg_order_value
FROM tpch.tiny.orders
GROUP BY DATE_TRUNC('month', orderdate)
ORDER BY month
```

## Top N Queries

```
Run this query:
SELECT 
    name,
    COUNT(*) as order_count
FROM tpch.tiny.customer c
JOIN tpch.tiny.orders o ON c.custkey = o.custkey
GROUP BY name
ORDER BY order_count DESC
LIMIT 10
```
