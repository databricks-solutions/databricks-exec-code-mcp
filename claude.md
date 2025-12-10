## Databricks MCP Code Execution Template via Command Execution API

Goal:
> Enable end-to-end development in Databricks using VibeCoding. Test code directly on clusters, then deploy with Databricks Asset Bundles (DABs).

---

### 🚀 Before Starting - User Configuration Required

When a user asks to build a pipeline, the AI assistant should **first collect the following information**:

#### 1. Databricks Workspace
Ask the user:
- **Workspace URL**: e.g., `https://dbc-xxxxx.cloud.databricks.com`
- **Personal Access Token (PAT)**: Generated from Databricks User Settings → Developer → Access Tokens
- **Catalog name**: Unity Catalog to use (must use underscores, not hyphens)
- **Cluster ID**: For testing code via the Command Execution API

#### 2. Databricks MCP Server 
For direct execution on Databricks clusters:
```json
{
  "mcpServers": {
    "databricks-dev-mcp": {
      "type": "http",
      "url": "http://localhost:8000/message"
    }
  }
}
```

---

### 📦 Packaging & Deployment Standards

#### 1. Development Workflow
The workflow has two phases:

**Phase 1: Test & Iterate (MCP Command Execution)**
- Use `databricks-dev-mcp` MCP to run code directly on a Databricks cluster
- Fetch execution results via the Databricks Command Execution API
- Debug errors with real cluster output
- Iterate until code works correctly

**Phase 2: Package & Deploy (DABs)**
- Once code is tested, package it with Databricks Asset Bundles
- Deploy the bundle as a production-ready pipeline
- Do NOT run anything locally or simulate results

#### 2. Always Use Databricks Asset Bundles (DABs)
- Package all Databricks code using `databricks.yml`
- Never create standalone scripts without bundle packaging
- Create the entire codebase locally inside its own folder within the main directory
- **After creating the DABs project, always run these commands to deploy:**
  1. `databricks bundle validate -t dev` - Validate the bundle configuration
  2. `databricks bundle deploy -t dev` - Deploy the bundle to Databricks
  3. `databricks bundle run <job_name> -t dev` - (Optional) Run the job immediately
- If CLI authentication fails, instruct the user to either:
  - Run `databricks auth login --host <workspace_url>` for interactive login
  - Set `DATABRICKS_HOST` and `DATABRICKS_TOKEN` environment variables

#### 3. Pipeline Structure
Organize code following this pattern:
```
project/
├── databricks.yml          # Bundle configuration
├── resources/              # Job definitions
│   └── training_job.yml
├── src/<project>/
│   └── notebooks/          # Databricks notebooks
│       ├── 01_data_prep.py
│       ├── 02_training.py
│       └── 03_validation.py
└── tests/                  # Unit tests (optional)
```

**⚠️ Important DABs Path Resolution:**
When using `include: - resources/*.yml` in `databricks.yml`, notebook paths in those resource files are resolved **relative to the resource file location**, not the bundle root. For example, if your job YAML is in `resources/`, use `notebook_path: ../src/notebooks/my_notebook.py` (with `../` to navigate back to bundle root) instead of `notebook_path: src/notebooks/my_notebook.py`.

#### 4. Parameterize Everything - No Hard-Coded Values
- Use bundle variables: `${var.catalog}`, `${var.schema}`, `${bundle.target}`
- Workspace paths: `${workspace.current_user.userName}`
- Pass parameters via `dbutils.widgets` in notebooks

#### 5. Multi-Environment Support
Configure targets in `databricks.yml`:
- `dev` - Development (user workspace)
- `staging` - Pre-production testing (optional)
- `prod` - Production deployment (optional)

---

### 🧠 AI Assistant Workflow

When asked to build and deploy a pipeline, the AI should:

1. **Collect configuration** (workspace, catalog, cluster ID) from the user
2. **Test code on Databricks** using MCP Command Execution API
3. **Debug and iterate** until code works correctly
4. **Create the DABs project** structure with all necessary files
5. **Validate the bundle** using `databricks bundle validate`
6. **Deploy the bundle** using `databricks bundle deploy`
7. **Verify deployment** in Databricks workspace

---

### 🔒 Safety & Permissions

- Never hard-code tokens or secrets in files
- Use environment variables for authentication
- Use `dbutils.widgets` for parameterization in notebooks
- All API calls must use secure authentication

---

### 🛠️ Serverless Compute Considerations

When deploying to serverless-only workspaces:
- Do NOT define `new_cluster` in job tasks
- Use `%pip install <package>` in notebooks for dependencies
- Use `try/except` for `dbutils.widgets.get()` (serverless has limited widget support)
- Test with `databricks bundle validate` before deployment

---

### 📚 Reference Links

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [MLOps Deployment Patterns](https://docs.databricks.com/aws/en/machine-learning/mlops/deployment-patterns#deploy-code-recommended)
