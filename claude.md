## Databricks MCP Code Execution Template via Command Execution API

Goal:
> Enable end-to-end development in Databricks using VibeCoding, with CI/CD support via GitHub Actions. Can be applied to general development or ML pipelines.

---

### 🚀 Before Starting - User Configuration Required

When a user asks to deploy an pipeline, the AI assistant should **first collect the following information**:

#### 1. Databricks Workspace
Ask the user:
- **Workspace URL**: e.g., `https://dbc-xxxxx.cloud.databricks.com`
- **Personal Access Token (PAT)**: Generated from Databricks User Settings → Developer → Access Tokens
- **Catalog name**: Unity Catalog to use (must use underscores, not hyphens)
- **Cluster ID** (optional): If using a specific all-purpose cluster

#### 2. GitHub Repository
Ask the user:
- **Repository name**: Where to push the DABs project (e.g., `my-mlops-project`)
- **Repository owner**: GitHub username or organization

#### 3. GitHub MCP Server
Verify the user has the GitHub MCP server configured in their `.cursor/mcp.json` or Claude settings:
```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer <GITHUB_TOKEN>"
      }
    }
  }
}
```

#### 4. Databricks MCP Server (Optional)
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

### 🔐 GitHub Secrets Setup

**Instruct the user** to configure these secrets in their GitHub repository:

1. Go to: `https://github.com/<owner>/<repo>/settings/secrets/actions`
2. Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `DATABRICKS_HOST` | `https://dbc-xxxxx.cloud.databricks.com` | Workspace URL (no trailing slash) |
| `DATABRICKS_TOKEN` | `dapi...` | Personal Access Token |

**Important**: These secrets enable GitHub Actions to authenticate with Databricks for CI/CD deployments.

---

### 📦 Packaging & Deployment Standards

#### 1. General Deployment Instructions
- When the user says or asks to "deploy the code or test it to Databricks", use the databricks-dev-mcp MCP you have it available.
- When the user only asks to deploy the ML pipeline or any other pipeline end-to-end in Databricks, you should package the code with dabs and deploy the bundle as a pipeline in Databricks first and then additionally ask about GitHub Actions settings.
- Do NOT run anything locally or simulate results.
- Create the entire codebase locally inside its own folder within the main directory (the vibe-databricks directory). Please don’t place the new files directly into the main directory — otherwise they will mix with the existing vibe-code setup. 
- After any code change:
  1. Run the updated code on Databricks using the MCP
  2. Fetch execution results via the Databricks Command Execution API
  3. Debug errors with real cluster output
- When the workflow runs on GitHub (Actions) please check after submission if pipline was successful. If the workflow crashes in GitHub Actions, immediately inform the user and show a plan to fix the issue, including error logs and remediation steps.


#### 2. Always Use Databricks Asset Bundles (DABs)
- Package all Databricks code using `databricks.yml`
- Validate bundles before deployment: `databricks bundle validate -t <target>`
- Never create standalone scripts without bundle packaging

#### 3. Pipeline Structure
Organize code following the this pattern:
```
project/
├── databricks.yml          # Bundle configuration
├── resources/              # Job definitions
│   └── training_job.yml
├── config/                 # Environment configs
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
├── src/<project>/
│   ├── training/           # Training notebooks
│   ├── validation/         # Model validation
│   └── deployment/         # Deployment scripts
├── tests/                  # Unit tests
└── .github/workflows/      # CI/CD pipelines
    └── ci.yml
```
**⚠️ Important DABs Path Resolution:**
When using `include: - resources/*.yml` in `databricks.yml`, notebook paths in those resource files are resolved **relative to the resource file location**, not the bundle root. For example, if your job YAML is in `resources/`, use `notebook_path: ../src/notebooks/my_notebook.py` (with `../` to navigate back to bundle root) instead of `notebook_path: src/notebooks/my_notebook.py`.

#### 4. Parameterize Everything - No Hard-Coded Values
- Use bundle variables: `${var.catalog}`, `${var.schema}`, `${bundle.target}`
- Workspace paths: `${workspace.current_user.userName}`
- Environment-specific configs in `config/*.yaml`

#### 5. Multi-Environment Support
Always configure three targets in `databricks.yml`:
- `dev` - Development (user workspace)
- `staging` - Pre-production testing
- `prod` - Production deployment

---

### 🔄 CI/CD Pipeline Setup

The AI should create a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. **Validates** the bundle on every push
2. **Runs tests** for Python code
3. **Deploys to dev** on `develop` branch or manual trigger
4. **Deploys to staging** on `main` branch
5. **Deploys to prod** on `main` branch (after staging)

### CI/CD Requirements:
- Use the **new Databricks CLI** (not `databricks-cli` pip package)
- Install via: `curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh`
- Authenticate using `DATABRICKS_HOST` and `DATABRICKS_TOKEN` secrets

---

### 🧠 AI Assistant Workflow

When being asked to deploy and manage a complete CI/CD end-to-end ML pipeline with Github Actions, the AI should:

1. **Collect configuration** (workspace, catalog, repo) from the user
2. **Create the DABs project** structure with all necessary files
3. **Push to GitHub** using the GitHub MCP server
4. **Instruct user** to add GitHub secrets
5. **Trigger deployment** via workflow dispatch
6. **Monitor and debug** any failures
7. **Verify deployment** in Databricks workspace

---

### 🔒 Safety & Permissions

- Never hard-code tokens or secrets in files
- Use GitHub secrets for CI/CD authentication
- Use environment variables or widgets in notebooks
- All API calls must use secure authentication

---

### 🛠️ Serverless Compute Considerations

When deploying to serverless-only workspaces:
- Do NOT define `new_cluster` in job tasks
- Use `%pip install <package>` in notebooks for dependencies
- Use `try/except` for `dbutils.widgets.get()` (serverless has limited widget support)
- Test locally with `databricks bundle validate` before deployment

---

### 📚 Reference Links

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [MLOps Deployment Patterns](https://docs.databricks.com/aws/en/machine-learning/mlops/deployment-patterns#deploy-code-recommended)
- [GitHub Actions for Databricks](https://github.com/databricks/setup-cli)
