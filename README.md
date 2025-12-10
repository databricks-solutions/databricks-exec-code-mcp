## Databricks MCP Code Execution Template

This template enables AI-assisted development in Databricks by leveraging the Databricks Command Execution API through an MCP server. Test code directly on clusters, then deploy with Databricks Asset Bundles (DABs).

### 🎯 What This Does

This template enables AI assistants to:
- ✅ Run and test code directly on Databricks clusters via the Command Execution API
- ✅ Create Databricks Asset Bundles (DABs) projects
- ✅ Deploy pipelines to multiple environments (dev/staging/prod)
- ✅ All from natural language prompts!

**Just describe what you want → AI builds, tests the code on Databricks, and deploys the complete pipeline.**

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

#### 2. Start the MCP Server

```bash
python mcp_tools/tools.py
```

The server runs at:
```
http://localhost:8000
```

#### 3. Configure Your AI Client

Add the following to your MCP configuration:

**For Cursor** (`~/.cursor/mcp.json`):
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

**For Claude Code** (`~/.config/claude/mcp.json`):
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

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": [
    {
      "id": "databricks-dev-mcp",
      "type": "http",
      "url": "http://localhost:8000/message"
    }
  ]
}
```

Restart your AI client after configuration.

#### 4. Prepare Your Credentials

You'll need:
- **Databricks Workspace URL**: `https://dbc-xxxxx.cloud.databricks.com`
- **Databricks PAT Token**: Generate from User Settings → Developer → Access Tokens
- **Unity Catalog Name**: e.g., `my_catalog`
- **Cluster ID**: For testing code via Command Execution API

#### 5. Include Context for AI

**For Cursor:**
Add the `claude.md` file to your project:
1. Place it in `.cursor/claude.md` in your project root, OR
2. Go to Settings → Rules and Commands → Toggle to include claude.md

**For Claude Code:**
Navigate to the directory containing the `claude.md` file.


#### 6. Example prompts

To start chatting with the AI-assistant, you can also leverage some examples in [`example_prompts`](./example_prompts).

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
