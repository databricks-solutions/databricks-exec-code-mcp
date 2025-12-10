# 💬 Example Prompt - ML Pipeline

Copy and paste this prompt to get started:

```
Check @CLAUDE.md

Please use cluster ID <YOUR_CLUSTER_ID> to create the context and do your work. 

Follow the rules in the claude.md file.

The task is to train a model on the Titanic dataset:

- Create a new schema in which we will log everything
- Download the data and save in a Delta table
- Do descriptive statistics and EDA
- Build a training pipeline with hyperparameter optimization
- Set up MLflow experiment logging
- Deploy the model as a serving endpoint
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

