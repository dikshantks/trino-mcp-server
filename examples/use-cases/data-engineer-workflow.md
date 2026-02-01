# Data Engineer Workflow

A typical workflow for data engineers using the Trino MCP server.

## 1. Initial Database Exploration

When working with a new database or schema:

```
1. Show me all catalogs
2. What schemas are in the [catalog] catalog?
3. List all tables in [catalog].[schema]
```

## 2. Understanding Table Structure

Before writing queries, understand the data structure:

```
1. Describe the [table] table
2. Show columns for [table]
3. Get statistics for [table]
4. Show me 10 sample rows from [table]
```

## 3. Data Quality Checks

Verify data quality before processing:

```
1. Get statistics for [table] to see row counts
2. Run: SELECT COUNT(*) FROM [table] WHERE [condition]
3. Check for nulls: SELECT COUNT(*) FROM [table] WHERE [column] IS NULL
4. Check distinct values: SELECT DISTINCT [column] FROM [table] LIMIT 20
```

## 4. Schema Validation

Verify expected columns exist:

```
Run: DESCRIBE [table]
```

Then verify expected columns are present and have correct types.

## 5. Data Sampling

Sample data to understand patterns:

```
Show me 20 sample rows from [table]
```

## 6. Query Development

Develop and test queries incrementally:

```
1. Start with simple SELECT: SELECT * FROM [table] LIMIT 10
2. Add filters: SELECT * FROM [table] WHERE [condition] LIMIT 10
3. Add aggregations: SELECT [columns], COUNT(*) FROM [table] GROUP BY [columns]
4. Add joins as needed
```

## 7. Performance Testing

Before running large queries:

```
1. Get table statistics to understand size
2. Test with LIMIT clauses first
3. Use EXPLAIN to understand query plan: EXPLAIN SELECT ...
```

## Example Complete Workflow

```
1. Show me all catalogs
2. What schemas are in the sales catalog?
3. List tables in sales.raw
4. Describe the transactions table
5. Get statistics for transactions
6. Show me 10 sample rows from transactions
7. Run: SELECT COUNT(*) FROM sales.raw.transactions WHERE date = CURRENT_DATE
```
