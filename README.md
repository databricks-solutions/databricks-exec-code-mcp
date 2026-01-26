## Databricks MCP Code Execution Template

This template enables AI-assisted development in Databricks by leveraging the Databricks Command Execution API through an MCP server. Test code directly on clusters, then deploy with Databricks Asset Bundles (DABs).

### 🎯 What This Does

- ✅ Run and test code directly on Databricks clusters
- ✅ Auto-select clusters - no need to specify a cluster ID
- ✅ Create and deploy Databricks Asset Bundles (DABs)
- ✅ All from natural language prompts!

**Just describe what you want → AI builds, tests the code on Databricks, and deploys the complete pipeline.**

---

### 🚀 Quick Start (Recommended Workflow)

#### Step 1: Set Up the MCP Server (One Time)

Clone and set up the MCP server somewhere on your machine:

```bash
git clone https://github.com/databricks-solutions/databricks-exec-code-mcp.git
cd databricks-exec-code-mcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Step 2: Configure Databricks Credentials

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=dapi_your_token_here
```

**To get your Personal Access Token (PAT):** Databricks workspace → Profile → Settings → Developer → Access Tokens → Generate new token

#### Step 3: Start a New Project

Create your project directory and install the Databricks skills:

```bash
# Create and enter your project
mkdir my-databricks-project && cd my-databricks-project

# Install skills for your AI client (downloads from remote)
curl -sSL https://raw.githubusercontent.com/databricks-solutions/databricks-exec-code-mcp/main/install_skills.sh | bash -s -- --cursor
# Or for Claude Code:
curl -sSL https://raw.githubusercontent.com/databricks-solutions/databricks-exec-code-mcp/main/install_skills.sh | bash -s -- --claude
# Or for both:
curl -sSL https://raw.githubusercontent.com/databricks-solutions/databricks-exec-code-mcp/main/install_skills.sh | bash -s -- --all
```

This creates:
- **Cursor**: `.cursor/rules/` with Databricks rules
- **Claude Code**: `.claude/skills/` with Databricks skills

#### Step 4: Configure Your AI Client

Point your AI client to the MCP server you set up in Step 1.

**For Cursor** — create `.cursor/mcp.json` in your project:
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

**For Claude Code** — run in your project:
```bash
claude mcp add-json databricks '{"command":"/path/to/databricks-exec-code-mcp/.venv/bin/python","args":["/path/to/databricks-exec-code-mcp/mcp_tools/tools.py"]}'
```

> Replace `/path/to/databricks-exec-code-mcp` with the actual path from Step 1.

#### Step 5: Start Prompting!

> 💡 **Smart Cluster Selection**: If no `cluster_id` is provided, the MCP server automatically finds a running cluster in your workspace.

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
| **Direct Cluster Execution** | Test code on Databricks clusters via Databricks Execution API|
| **DABs Packaging** | Production-ready bundle deployment |
| **Multi-Environment** | Support for dev/staging/prod targets |
| **Unity Catalog** | Models and data registered to UC for governance |
| **MLflow Tracking** | Experiment tracking and model versioning |

---

### 📚 Resources

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [MLOps Deployment Patterns](https://docs.databricks.com/aws/en/machine-learning/mlops/deployment-patterns)
- [MCP Specification](https://modelcontextprotocol.io/)
- [SKILLS](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

---

### 📜 License

© 2025 Databricks, Inc. All rights reserved. The source in this project is provided subject to the [Databricks License](LICENSE.md).

#### Third-Party Licenses

| Package | License | Copyright |
|---------|---------|-----------|
| [mcp](https://github.com/modelcontextprotocol/python-sdk) | MIT License | Copyright (c) 2024 Anthropic |
| [requests](https://github.com/psf/requests) | Apache License 2.0 | Copyright 2019 Kenneth Reitz |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | BSD 3-Clause License | Copyright (c) 2014, Saurabh Kumar |
