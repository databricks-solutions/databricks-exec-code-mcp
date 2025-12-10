# 💬 Example Prompt - Data Engineering Pipeline

Copy and paste this prompt to get started:

```
Check @CLAUDE.md

Please use cluster ID <YOUR_CLUSTER_ID> to create the context and do your work. 

Follow the rules in the claude.md file.

The task is to build a Data Engineering pipeline using Medallion Architecture and deploy it in Databricks:

- Create a new schema/catalog to log all datasets and transformations.
- Use the raw data from a source table in a certain catalog/schema.
- Perform transformations to clean and standardize data, storing results in the Silver layer.
- Aggregate and enrich data as required, storing results in the Gold layer.
- Ensure all tables have proper metadata (column types, descriptions, primary/foreign keys where applicable)
- Deploy the pipeline

Configuration:
- Catalog to use: <YOUR_CATALOG>
- Databricks workspace: <YOUR_WORKSPACE_URL>

Please start by checking the available MCP servers and let me know if you can use them.
```

---

## 🔧 Replace the Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `<YOUR_CLUSTER_ID>` | Your Databricks cluster ID | `1124-191600-6iri9ssy` |
| `<YOUR_CATALOG>` | Your Unity Catalog name | `my_mlops_catalog` |
| `<YOUR_WORKSPACE_URL>` | Your Databricks workspace URL | `https://dbc-xxxxx.cloud.databricks.com` |

