# Exploring Database Structure

This guide shows how to explore a Trino database using the MCP server tools.

## Step 1: List All Catalogs

```
Show me all available catalogs in Trino
```

This uses the `show_catalogs` tool to discover what catalogs are available.

## Step 2: Explore Schemas

```
What schemas are available in the tpch catalog?
```

This uses the `show_schemas` tool to list schemas in a specific catalog.

## Step 3: List Tables

```
Show me all tables in the tpch.tiny schema
```

This uses the `show_tables` tool to discover tables in a schema.

## Step 4: Understand Table Structure

```
Describe the structure of the customer table in tpch.tiny
```

This uses the `describe_table` tool to see column names, types, and properties.

## Step 5: Sample Data

```
Show me 5 sample rows from the orders table
```

This uses the `sample_table` tool to preview actual data.

## Complete Exploration Workflow

You can combine these steps:

```
1. Show me all catalogs
2. What schemas are in the tpch catalog?
3. List all tables in tpch.tiny
4. Describe the customer table
5. Show me 10 sample rows from customer
```
