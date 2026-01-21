## Databricks MCP Code Execution Template

This template enables AI-assisted development in Databricks by leveraging the Databricks Command Execution API through an MCP server. Test code directly on clusters, then deploy with Databricks Asset Bundles (DABs).

### 🎯 What This Does

This template enables AI assistants to:
- ✅ Run and test code directly on Databricks clusters via the Command Execution API
- ✅ Auto-select clusters - no need to specify a cluster ID, automatically connects to a running cluster
- ✅ Create Databricks Asset Bundles (DABs) projects
- ✅ Deploy pipelines to multiple environments (dev/staging/prod)
- ✅ All from natural language prompts!

**Just describe what you want → AI builds, tests the code on Databricks, and deploys the complete pipeline.**

> 💡 **Smart Cluster Selection**: If no `cluster_id` is provided, the MCP server automatically finds a running cluster in your workspace (prioritizing clusters with "interactive", "general", or "all-purpose" in the name).

---

### ⚙️ Prerequisites - Set Up Environment Variables

Before running the MCP server, configure your Databricks credentials as environment variables:

```bash
# Set your Databricks workspace URL (no trailing slash)
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Set your Databricks Personal Access Token
export DATABRICKS_TOKEN=dapi_your_token_here
```

**To get your Personal Access Token (PAT):**
1. Go to your Databricks workspace
2. Click your profile icon → **Settings** → **Developer**
3. Click **Manage** under Access Tokens → **Generate new token**
4. Copy the token (it won't be shown again!)

> 💡 **Tip**: Add these exports to your `~/.zshrc` or `~/.bashrc` to persist them across terminal sessions.

---

### 🚀 Quick Start

#### 1. Clone This Repository

```bash
cd databricks-exec-code-mcp
```

#### 2. Install Requirements

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Configure Your AI Client

Add the MCP server to your configuration. Use the path to your cloned repo:

**For Cursor** (`.cursor/mcp.json` in your project, or global `~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "/path/to/databricks-exec-code-mcp/.venv/bin/python",
      "args": ["/path/to/databricks-exec-code-mcp/mcp_tools/tools.py"]
    }
  }
}
```

**For Claude Code** (`.claude/mcp.json` in your project):
```json
{
  "mcpServers": {
    "databricks": {
      "command": "/path/to/databricks-exec-code-mcp/.venv/bin/python",
      "args": ["/path/to/databricks-exec-code-mcp/mcp_tools/tools.py"]
    }
  }
}
```

> 💡 **Tip**: Replace `/path/to/databricks-exec-code-mcp` with the actual path to your cloned repo.

Restart your AI client after configuration.

#### 4. Install Skills

Install the Databricks skills to teach your AI assistant how to work with Databricks:

```bash
# Install for both Cursor and Claude Code
./install_skills.sh --all

# Or install for a specific client
./install_skills.sh --cursor
./install_skills.sh --claude
```

This installs skills to:
- **Cursor**: `.cursor/rules/`
- **Claude Code**: `.claude/skills/`

#### 5. Start Building!

Just describe what you want in natural language:

**Data Engineering:**
> "Build a Data Engineering pipeline using Medallion Architecture on the NYC Taxi dataset and deploy it with DABs"

**Machine Learning:**
> "Train a classification model on the Titanic dataset, register it to Unity Catalog, and deploy as a DAB job"

**Quick Test:**
> "Run a SQL query to show the top 10 tables in my catalog"

---

### 📁 What Gets Generated

The AI will create a complete DABs project:

```
your-project/
├── databricks.yml              # DABs configuration
├── resources/
│   └── training_job.yml        # Databricks job definition
├── src/<project>/
│   └── notebooks/
│       ├── 01_data_prep.py
│       ├── 02_training.py
│       └── 03_validation.py
└── tests/                      # Unit tests (optional)
```

---

### 🌟 Features

| Feature | Description |
|---------|-------------|
| **Direct Cluster Execution** | Test code on Databricks clusters via MCP |
| **DABs Packaging** | Production-ready bundle deployment |
| **Multi-Environment** | Support for dev/staging/prod targets |
| **Unity Catalog** | Models and data registered to UC for governance |
| **MLflow Tracking** | Experiment tracking and model versioning |

---

### 🛠️ Troubleshooting

#### MCP Server Connection Issues
1. Ensure the MCP server is running: `python mcp_tools/tools.py`
2. Verify environment variables are set: `echo $DATABRICKS_HOST`
3. Check your AI client's MCP configuration

#### Databricks Authentication
If CLI authentication fails:
- Run `databricks auth login --host <workspace_url>` for interactive login
- Or set `DATABRICKS_HOST` and `DATABRICKS_TOKEN` environment variables

---

### 📚 Resources

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [MLOps Deployment Patterns](https://docs.databricks.com/aws/en/machine-learning/mlops/deployment-patterns)
- [MCP Specification](https://modelcontextprotocol.io/)

---

### 📜 License

© 2025 Databricks, Inc. All rights reserved. The source in this project is provided subject to the [Databricks License](LICENSE.md).

#### Third-Party Licenses

| Package | License | Copyright |
|---------|---------|-----------|
| [FastAPI](https://github.com/tiangolo/fastapi) | MIT License | Copyright (c) 2018 Sebastián Ramírez |
| [requests](https://github.com/psf/requests) | Apache License 2.0 | Copyright 2019 Kenneth Reitz |
| [uvicorn](https://github.com/encode/uvicorn) | BSD 3-Clause License | Copyright © 2017-present, Encode OSS Ltd |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | BSD 3-Clause License | Copyright (c) 2014, Saurabh Kumar |
