## Databricks MCP Code Execution Template

**Goal:** Enable end-to-end development in Databricks using AI assistance. Test code directly on clusters via MCP, then deploy with Databricks Asset Bundles (DABs).

---

## Critical Workflow Rules

**These rules override everything else and must ALWAYS be followed:**

### 1. MCP Command Execution (AUTOMATIC)
- **MCP commands always run automatically** on the Databricks cluster
- **No confirmation required** for MCP execution
- **Never simulate execution locally** - always use real cluster
- **Return complete cluster output** to the user

### 2. Bundle Validation & Deployment (AUTOMATIC)
- **`databricks bundle validate`** runs automatically (no confirmation)
- **`databricks bundle deploy`** runs automatically (no confirmation)
- Fix any validation errors and re-run

### 3. Bundle Job Execution (REQUIRES CONFIRMATION)
- **`databricks bundle run <job>` NEVER runs automatically**
- **Always ask user explicitly:** "Do you want to run the deployed job now?"
- Only execute if user confirms
- Report run status, results, and any errors

### 4. Security (ALWAYS)
- **Never store or print access tokens**
- **Never embed secrets** in code or notebooks
- **Use environment variables** for authentication
- **Use secure API calls** only

### 5. When Unsure
- **Ask the user** before proceeding

---

## Implementation Details

All implementation details (project structure, parameterization, serverless compute, best practices, etc.) are provided by **Claude Code Skills**:

- **databricks-testing** - Execute code on clusters via MCP
- **databricks-unity-catalog** - Manage Unity Catalog resources
- **databricks-bundle-deploy** - Package and deploy DABs
- **databricks-ml-pipeline** - End-to-end ML workflows
- **databricks-data-engineering** - Medallion architecture pipelines

Skills auto-trigger based on user requests and contain comprehensive guidance for each workflow.

---

## References

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks MLOps Patterns](https://docs.databricks.com/machine-learning/mlops/mlops-workflow.html)
