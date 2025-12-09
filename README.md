##  Databricks MCP Code Execution Template via Command Execution API
This template streamlines and accelerates development in Databricks by leveraging the Databricks Command Execution API, exposed through an MCP server, to run and test code directly in Databricks. It also enables end-to-end pipeline deployment using vibecoding capabilities.

### 🎯 What This Does

This template enables AI assistants to:
- ✅ Run, execute, test code directly to Databricks via the command execution API
- ✅ Create Databricks Asset Bundles (DABs) projects
- ✅ Set up CI/CD with GitHub Actions
- ✅ Deploy to multiple environments (dev/staging/prod)
- ✅ All from natural language prompts!

**Just describe what you want → AI builds, tests the code and deploys the complete pipeline.**

---

### 🚀 Quick Start

#### 1. Clone This Repository

```bash
cd databricks-exec-code-mcp
```

#### 2. Configure MCP Servers

Start the MCP Server

```bash
python mcp_tools/tools.py
```
The server runs at:
```
http://localhost:8000
```

Add the following to your MCP configuration:

**For Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "github": {
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer <YOUR_GITHUB_TOKEN>"
      }
    },
    "databricks-dev-mcp": {
        "type": "http",
        "url": "http://localhost:8000/message"
    }
  }
}
```

Restart Cursor.

---

#### Claude Code

File: `~/.config/claude/mcp.json`

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_TOKEN}"
      }
    },
    "databricks-dev-mcp": {
      "type": "http",
      "url": "http://localhost:8000/message"
    }
  }
}
```

Restart Claude Code.

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_GITHUB_TOKEN"
      }
    },
    "databricks-dev-mcp": {
      "type": "http",
      "url": "http://localhost:8000/message"
    }
  }
}
```

#### 3. Prepare Your Credentials

You'll need:
- **Databricks Workspace URL**: `https://dbc-xxxxx.cloud.databricks.com`
- **Databricks PAT Token**: Generate from User Settings → Developer → Access Tokens
- **Unity Catalog Name**: e.g., `my_catalog`
- **GitHub Repository**: Where to push the generated project

#### 4. Open in Your AI Client

Open this folder in Cursor or add it to Claude Desktop, then start chatting 💬

 - In order to get started with some prompts, see [example_prompts/prompts.md](./example_prompts/prompts.md) for some ready-to-use examples.

---

#### 5. Default context to agentic coding tools

**For Cursor**

Include the claude.md file following any of the below options:
  1. Navigate and add claude.md file in .cursor folder in your project root like project-name/.cursor/claude.md 
  2. Go to Settings-> Rules and Commands -> Toggle the button to include the claude.md in context and use @claude before your promp when interacting in the chat window.

**For Claude code**

Navigate to the directory of your project where the claude.md file is residing i.e mcp-accl/vibe-databricks/





---

### 🔐 GitHub Secrets Setup

After the AI creates your GitHub repository, add these secrets:

1. Go to: `https://github.com/<owner>/<repo>/settings/secrets/actions`
2. Add:

| Secret Name | Value |
|-------------|-------|
| `DATABRICKS_HOST` | `https://dbc-xxxxx.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | `dapi...` (your PAT token) |

---

### 📁 What Gets Generated

The AI will create a complete the project:

```
your-project/
├── databricks.yml              # DABs configuration
├── requirements.txt            # Python dependencies
├── resources/
│   └── training_job.yml        # Databricks job definition
├── config/
│   ├── dev.yaml               # Dev environment config
│   ├── staging.yaml           # Staging config
│   └── prod.yaml              # Production config
├── src/<project>/
│   ├── training/
│   │   ├── feature_engineering.py
│   │   └── train.py
│   └── validation/
│       └── validate_model.py
├── tests/
│   └── test_config.py
└── .github/workflows/
    └── ci.yml                  # CI/CD pipeline
```

---

### 🌟 Features

| Feature | Description |
|---------|-------------|
| **Multi-Environment** | Automatic dev/staging/prod deployments |
| **Unity Catalog** | Models registered to UC for governance |
| **MLflow Tracking** | Experiment tracking and model versioning |
| **GitHub Actions CI/CD** | Automated validation and deployment |

---

### 🛠️ Troubleshooting

#### IP ACL Errors
If you see "Source IP address is blocked", your workspace has IP restrictions. Options:
1. Add GitHub Actions IP ranges to your workspace IP Access List
2. Use a self-hosted GitHub runner

---

### 📚 Resources

- [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- [MLOps Deployment Patterns](https://docs.databricks.com/aws/en/machine-learning/mlops/deployment-patterns)
- [MCP Specification](https://modelcontextprotocol.io/)
- [GitHub Actions for Databricks](https://github.com/databricks/setup-cli)

