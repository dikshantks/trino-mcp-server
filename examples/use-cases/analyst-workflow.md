# Data Analyst Workflow

A typical workflow for data analysts using the Trino MCP server.

## 1. Data Discovery

Start by exploring available data:

```
1. Show me all catalogs
2. What schemas are available?
3. What tables are in [schema]?
```

## 2. Understanding the Data

Get familiar with the data structure and content:

```
1. Describe [table] to see columns and types
2. Show me 10 sample rows from [table]
3. Get statistics for [table] to see row counts
```

## 3. Exploratory Analysis

Start with simple queries to understand patterns:

```
Run: SELECT [column], COUNT(*) 
FROM [table] 
GROUP BY [column] 
ORDER BY COUNT(*) DESC 
LIMIT 10
```

## 4. Building Insights

Combine data from multiple tables:

```
Run: SELECT 
    c.category,
    SUM(s.amount) as total_sales,
    COUNT(DISTINCT s.customer_id) as unique_customers
FROM sales s
JOIN products p ON s.product_id = p.id
JOIN categories c ON p.category_id = c.id
GROUP BY c.category
ORDER BY total_sales DESC
```

## 5. Time Series Analysis

Analyze trends over time:

```
Run: SELECT 
    DATE_TRUNC('month', order_date) as month,
    COUNT(*) as orders,
    SUM(amount) as revenue
FROM orders
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month
```

## 6. Comparative Analysis

Compare different segments:

```
Run: SELECT 
    region,
    AVG(order_value) as avg_order_value,
    COUNT(*) as order_count
FROM orders
GROUP BY region
ORDER BY avg_order_value DESC
```

## 7. Data Validation

Verify data quality:

```
Run: SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(CASE WHEN amount IS NULL THEN 1 ELSE 0 END) as null_amounts
FROM orders
```

## Example Analysis Session

```
1. Show me all catalogs
2. What tables are in sales.analytics?
3. Describe the monthly_sales table
4. Show me 5 sample rows
5. Run: SELECT 
    product_category,
    SUM(revenue) as total_revenue,
    AVG(revenue) as avg_revenue
   FROM sales.analytics.monthly_sales
   GROUP BY product_category
   ORDER BY total_revenue DESC
```
