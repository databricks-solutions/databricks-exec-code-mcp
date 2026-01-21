#!/usr/bin/env python3
"""
Databricks Command MCP Server (stdio transport)
Implements the MCP protocol over stdio for use with Claude/Cursor.
"""
import os
import sys
import json
import time
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HOST = os.getenv("DATABRICKS_HOST")
TOKEN = os.getenv("DATABRICKS_TOKEN")

if not HOST or not TOKEN:
    print("Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


# === Cluster Discovery Functions ===

def get_workspace_clusters(include_stopped: bool = False) -> list:
    """
    Retrieve all user-created clusters from the workspace.
    """
    try:
        resp = requests.get(
            f"{HOST}/api/2.0/clusters/list",
            headers=HEADERS
        )
        resp.raise_for_status()
        all_clusters = resp.json().get("clusters", [])
        
        user_sources = ["UI", "API"]
        clusters = []
        
        for c in all_clusters:
            source = c.get("cluster_source", "")
            state = c.get("state", "")
            
            if source not in user_sources:
                continue
            
            if not include_stopped and state not in ["RUNNING", "PENDING", "RESIZING"]:
                continue
            
            clusters.append({
                "cluster_id": c.get("cluster_id"),
                "cluster_name": c.get("cluster_name", ""),
                "state": state,
                "creator": c.get("creator_user_name", ""),
            })
        
        return clusters
    except Exception:
        return []


def find_available_cluster() -> Optional[str]:
    """
    Find an available running cluster for code execution.
    """
    clusters = get_workspace_clusters(include_stopped=False)
    
    if not clusters:
        return None
    
    priority_keywords = ["interactive", "general", "all-purpose", "dev"]
    
    for keyword in priority_keywords:
        for c in clusters:
            if keyword in c["cluster_name"].lower():
                return c["cluster_id"]
    
    return clusters[0]["cluster_id"]


def _resolve_cluster_id(cluster_id: Optional[str]) -> tuple:
    """Resolve cluster_id, auto-selecting if not provided."""
    if cluster_id == "":
        cluster_id = None
    
    if cluster_id is not None:
        return cluster_id, None
    
    auto_cluster = find_available_cluster()
    
    if auto_cluster is not None:
        return auto_cluster, None
    
    all_clusters = get_workspace_clusters(include_stopped=True)
    
    if not all_clusters:
        return None, "No clusters found in workspace. Please create a cluster first."
    
    cluster_list = "\n".join(
        f"  - {c['cluster_name']} ({c['cluster_id']}) - {c['state']}"
        for c in all_clusters[:10]
    )
    error_msg = (
        f"No running cluster available. Please start one of these clusters or specify a cluster_id:\n{cluster_list}"
    )
    if len(all_clusters) > 10:
        error_msg += f"\n  ... and {len(all_clusters) - 10} more"
    
    return None, error_msg


# === MCP Tool Implementations ===

def list_clusters_impl(include_stopped: bool = False) -> str:
    """List all available clusters in the workspace."""
    clusters = get_workspace_clusters(include_stopped=include_stopped)
    
    if not clusters:
        return "No clusters found in workspace."
    
    output = f"Found {len(clusters)} cluster(s):\n\n"
    for c in clusters:
        state_icon = "🟢" if c["state"] == "RUNNING" else "🔴" if c["state"] == "TERMINATED" else "🟡"
        output += f"{state_icon} {c['cluster_name']}\n"
        output += f"   ID: {c['cluster_id']}\n"
        output += f"   State: {c['state']}\n"
        output += f"   Creator: {c['creator']}\n\n"
    
    return output


def create_context_impl(cluster_id: Optional[str] = None, language: str = "python") -> str:
    """Create a new execution context on Databricks cluster."""
    resolved_id, error = _resolve_cluster_id(cluster_id)
    if error:
        return f"Error: {error}"
    
    auto_selected = cluster_id is None or cluster_id == ""
    
    try:
        ctx_resp = requests.post(
            f"{HOST}/api/1.2/contexts/create",
            headers=HEADERS,
            json={"clusterId": resolved_id, "language": language}
        )
        ctx_resp.raise_for_status()
        context_id = ctx_resp.json()["id"]

        msg = f"Context created successfully!\n\nContext ID: {context_id}\nCluster ID: {resolved_id}\nLanguage: {language}"
        if auto_selected:
            msg += "\n\n(Cluster was auto-selected)"
        msg += "\n\nUse this context_id for subsequent commands to maintain state."
        
        return msg
    except Exception as e:
        return f"Error creating context: {str(e)}"


def execute_command_with_context_impl(cluster_id: str, context_id: str, code: str) -> str:
    """Execute code using an existing context."""
    try:
        cmd_resp = requests.post(
            f"{HOST}/api/1.2/commands/execute",
            headers=HEADERS,
            json={
                "clusterId": cluster_id,
                "contextId": context_id,
                "language": "python",
                "command": code
            }
        )
        cmd_resp.raise_for_status()
        command_id = cmd_resp.json()["id"]

        timeout = 120
        start_time = time.time()
        while True:
            status_resp = requests.get(
                f"{HOST}/api/1.2/commands/status",
                headers=HEADERS,
                params={
                    "clusterId": cluster_id,
                    "contextId": context_id,
                    "commandId": command_id
                }
            )
            status_resp.raise_for_status()
            status = status_resp.json()

            if status.get("status") in ["Finished", "Error", "Cancelled"]:
                break

            if time.time() - start_time > timeout:
                return "Error: Command timed out"

            time.sleep(2)

        results = status.get("results", {})
        result_type = results.get("resultType", "")

        if status.get("status") == "Error" or result_type == "error":
            error_msg = results.get("cause", results.get("summary", "Unknown error"))
            return f"Error: {error_msg}"

        result_data = results.get("data")
        return str(result_data) if result_data else "Success (no output)"

    except Exception as e:
        return f"Error: {str(e)}"


def destroy_context_impl(cluster_id: str, context_id: str) -> str:
    """Destroy an execution context."""
    try:
        ctx_resp = requests.post(
            f"{HOST}/api/1.2/contexts/destroy",
            headers=HEADERS,
            json={"clusterId": cluster_id, "contextId": context_id}
        )
        ctx_resp.raise_for_status()
        return f"Context {context_id} destroyed successfully!"
    except Exception as e:
        return f"Error destroying context: {str(e)}"


def databricks_command_impl(code: str, cluster_id: Optional[str] = None, language: str = "python") -> str:
    """Execute code on Databricks cluster (creates and destroys context automatically)."""
    resolved_id, error = _resolve_cluster_id(cluster_id)
    if error:
        return f"Error: {error}"
    
    try:
        # 1. Create execution context
        ctx_resp = requests.post(
            f"{HOST}/api/1.2/contexts/create",
            headers=HEADERS,
            json={"clusterId": resolved_id, "language": language}
        )
        ctx_resp.raise_for_status()
        context_id = ctx_resp.json()["id"]

        # 2. Submit command
        cmd_resp = requests.post(
            f"{HOST}/api/1.2/commands/execute",
            headers=HEADERS,
            json={
                "clusterId": resolved_id,
                "contextId": context_id,
                "language": language,
                "command": code
            }
        )
        cmd_resp.raise_for_status()
        command_id = cmd_resp.json()["id"]

        # 3. Poll for result
        timeout = 120
        start_time = time.time()
        while True:
            status_resp = requests.get(
                f"{HOST}/api/1.2/commands/status",
                headers=HEADERS,
                params={
                    "clusterId": resolved_id,
                    "contextId": context_id,
                    "commandId": command_id
                }
            )
            status_resp.raise_for_status()
            status = status_resp.json()

            if status.get("status") in ["Finished", "Error", "Cancelled"]:
                break

            if time.time() - start_time > timeout:
                return "Error: Command timed out"

            time.sleep(2)

        results = status.get("results", {})
        result_type = results.get("resultType", "")

        if status.get("status") == "Error" or result_type == "error":
            error_msg = results.get("cause", results.get("summary", "Unknown error"))
            return f"Error: {error_msg}"

        result_data = results.get("data")
        return str(result_data) if result_data else "Success (no output)"

    except Exception as e:
        return f"Error: {str(e)}"


# === Unity Catalog Functions ===

def list_catalogs_impl() -> str:
    """List all catalogs in Unity Catalog."""
    try:
        resp = requests.get(f"{HOST}/api/2.1/unity-catalog/catalogs", headers=HEADERS)
        resp.raise_for_status()
        catalogs = resp.json().get("catalogs", [])

        output = f"Found {len(catalogs)} catalogs:\n\n"
        for catalog in catalogs:
            output += f"📚 {catalog.get('name')}\n"
            if catalog.get('comment'):
                output += f"   Comment: {catalog.get('comment')}\n"
            output += f"   Owner: {catalog.get('owner')}\n\n"

        return output
    except Exception as e:
        return f"Error: {str(e)}"


def get_catalog_impl(catalog_name: str) -> str:
    """Get detailed information about a specific catalog."""
    try:
        resp = requests.get(f"{HOST}/api/2.1/unity-catalog/catalogs/{catalog_name}", headers=HEADERS)
        resp.raise_for_status()
        catalog = resp.json()

        output = f"📚 Catalog: {catalog.get('name')}\n"
        output += f"   Full Name: {catalog.get('full_name')}\n"
        output += f"   Owner: {catalog.get('owner')}\n"
        output += f"   Comment: {catalog.get('comment', 'N/A')}\n"

        return output
    except Exception as e:
        return f"Error: {str(e)}"


def list_schemas_impl(catalog_name: str) -> str:
    """List all schemas in a catalog."""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/schemas",
            headers=HEADERS,
            params={"catalog_name": catalog_name}
        )
        resp.raise_for_status()
        schemas = resp.json().get("schemas", [])

        output = f"Found {len(schemas)} schemas in catalog '{catalog_name}':\n\n"
        for schema in schemas:
            output += f"📁 {schema.get('name')}\n"
            if schema.get('comment'):
                output += f"   Comment: {schema.get('comment')}\n"
            output += f"   Owner: {schema.get('owner')}\n\n"

        return output
    except Exception as e:
        return f"Error: {str(e)}"


def get_schema_impl(full_schema_name: str) -> str:
    """Get detailed information about a specific schema."""
    try:
        resp = requests.get(f"{HOST}/api/2.1/unity-catalog/schemas/{full_schema_name}", headers=HEADERS)
        resp.raise_for_status()
        schema = resp.json()

        output = f"📁 Schema: {schema.get('name')}\n"
        output += f"   Full Name: {schema.get('full_name')}\n"
        output += f"   Catalog: {schema.get('catalog_name')}\n"
        output += f"   Owner: {schema.get('owner')}\n"
        output += f"   Comment: {schema.get('comment', 'N/A')}\n"

        return output
    except Exception as e:
        return f"Error: {str(e)}"


def list_tables_impl(catalog_name: str, schema_name: str) -> str:
    """List all tables in a schema."""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/tables",
            headers=HEADERS,
            params={"catalog_name": catalog_name, "schema_name": schema_name}
        )
        resp.raise_for_status()
        tables = resp.json().get("tables", [])

        output = f"Found {len(tables)} tables in {catalog_name}.{schema_name}:\n\n"
        for table in tables:
            output += f"📊 {table.get('name')}\n"
            output += f"   Type: {table.get('table_type')}\n"
            if table.get('comment'):
                output += f"   Comment: {table.get('comment')}\n"
            output += f"   Owner: {table.get('owner')}\n\n"

        return output
    except Exception as e:
        return f"Error: {str(e)}"


def get_table_impl(full_table_name: str) -> str:
    """Get detailed information about a specific table."""
    try:
        resp = requests.get(f"{HOST}/api/2.1/unity-catalog/tables/{full_table_name}", headers=HEADERS)
        resp.raise_for_status()
        table = resp.json()

        output = f"📊 Table: {table.get('name')}\n"
        output += f"   Full Name: {table.get('full_name')}\n"
        output += f"   Type: {table.get('table_type')}\n"
        output += f"   Owner: {table.get('owner')}\n"
        output += f"   Comment: {table.get('comment', 'N/A')}\n"

        columns = table.get('columns', [])
        if columns:
            output += f"\n   Columns ({len(columns)}):\n"
            for col in columns:
                output += f"     - {col.get('name')}: {col.get('type_name')}\n"

        return output
    except Exception as e:
        return f"Error: {str(e)}"


def create_schema_impl(catalog_name: str, schema_name: str, comment: Optional[str] = None) -> str:
    """Create a new schema in Unity Catalog."""
    try:
        payload = {"name": schema_name, "catalog_name": catalog_name}
        if comment:
            payload["comment"] = comment

        resp = requests.post(f"{HOST}/api/2.1/unity-catalog/schemas", headers=HEADERS, json=payload)
        resp.raise_for_status()
        schema = resp.json()

        output = f"✅ Schema created successfully!\n\n"
        output += f"📁 Schema: {schema.get('name')}\n"
        output += f"   Full Name: {schema.get('full_name')}\n"
        output += f"   Owner: {schema.get('owner')}\n"

        return output
    except Exception as e:
        return f"Error creating schema: {str(e)}"


def delete_schema_impl(full_schema_name: str) -> str:
    """Delete a schema from Unity Catalog."""
    try:
        resp = requests.delete(f"{HOST}/api/2.1/unity-catalog/schemas/{full_schema_name}", headers=HEADERS)
        resp.raise_for_status()
        return f"✅ Schema '{full_schema_name}' deleted successfully!"
    except Exception as e:
        return f"Error deleting schema: {str(e)}"


def delete_table_impl(full_table_name: str) -> str:
    """Delete a table from Unity Catalog."""
    try:
        resp = requests.delete(f"{HOST}/api/2.1/unity-catalog/tables/{full_table_name}", headers=HEADERS)
        resp.raise_for_status()
        return f"✅ Table '{full_table_name}' deleted successfully!"
    except Exception as e:
        return f"Error deleting table: {str(e)}"


# === MCP Server (stdio transport) ===

TOOLS = [
    {
        "name": "list_clusters",
        "description": "List all available clusters in the workspace. Shows cluster ID, name, state, and creator.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_stopped": {
                    "type": "boolean",
                    "description": "Include stopped/terminated clusters (default: false)"
                }
            }
        }
    },
    {
        "name": "databricks_command",
        "description": "Execute code on a Databricks cluster. If cluster_id is not provided, automatically selects a running cluster. Creates and destroys context automatically (does NOT maintain state between calls).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code to execute"},
                "cluster_id": {"type": "string", "description": "Databricks cluster ID (optional - auto-selects if not provided)"},
                "language": {"type": "string", "description": "Language (python, scala, sql, r)", "default": "python"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "create_context",
        "description": "Create a new execution context on Databricks cluster. Returns a context_id for subsequent commands to maintain state. If cluster_id is not provided, auto-selects a running cluster.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Databricks cluster ID (optional)"},
                "language": {"type": "string", "description": "Language (python, scala, sql, r)", "default": "python"}
            }
        }
    },
    {
        "name": "execute_command_with_context",
        "description": "Execute code using an existing context. Maintains state between calls (variables, imports persist).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Databricks cluster ID"},
                "context_id": {"type": "string", "description": "Context ID from create_context"},
                "code": {"type": "string", "description": "Code to execute"}
            },
            "required": ["cluster_id", "context_id", "code"]
        }
    },
    {
        "name": "destroy_context",
        "description": "Destroy an execution context to free resources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Databricks cluster ID"},
                "context_id": {"type": "string", "description": "Context ID to destroy"}
            },
            "required": ["cluster_id", "context_id"]
        }
    },
    {
        "name": "list_catalogs",
        "description": "List all catalogs in Unity Catalog.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_catalog",
        "description": "Get detailed information about a specific catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {"catalog_name": {"type": "string", "description": "Name of the catalog"}},
            "required": ["catalog_name"]
        }
    },
    {
        "name": "list_schemas",
        "description": "List all schemas in a catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {"catalog_name": {"type": "string", "description": "Name of the catalog"}},
            "required": ["catalog_name"]
        }
    },
    {
        "name": "get_schema",
        "description": "Get detailed information about a specific schema.",
        "inputSchema": {
            "type": "object",
            "properties": {"full_schema_name": {"type": "string", "description": "Full schema name (catalog.schema)"}},
            "required": ["full_schema_name"]
        }
    },
    {
        "name": "list_tables",
        "description": "List all tables in a schema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "catalog_name": {"type": "string", "description": "Name of the catalog"},
                "schema_name": {"type": "string", "description": "Name of the schema"}
            },
            "required": ["catalog_name", "schema_name"]
        }
    },
    {
        "name": "get_table",
        "description": "Get detailed information about a specific table including columns.",
        "inputSchema": {
            "type": "object",
            "properties": {"full_table_name": {"type": "string", "description": "Full table name (catalog.schema.table)"}},
            "required": ["full_table_name"]
        }
    },
    {
        "name": "create_schema",
        "description": "Create a new schema in Unity Catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "catalog_name": {"type": "string", "description": "Name of the catalog"},
                "schema_name": {"type": "string", "description": "Name of the schema to create"},
                "comment": {"type": "string", "description": "Optional description"}
            },
            "required": ["catalog_name", "schema_name"]
        }
    },
    {
        "name": "delete_schema",
        "description": "Delete a schema from Unity Catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {"full_schema_name": {"type": "string", "description": "Full schema name (catalog.schema)"}},
            "required": ["full_schema_name"]
        }
    },
    {
        "name": "delete_table",
        "description": "Delete a table from Unity Catalog.",
        "inputSchema": {
            "type": "object",
            "properties": {"full_table_name": {"type": "string", "description": "Full table name (catalog.schema.table)"}},
            "required": ["full_table_name"]
        }
    }
]


def handle_tool_call(name: str, arguments: dict) -> str:
    """Route tool calls to implementations."""
    if name == "list_clusters":
        return list_clusters_impl(arguments.get("include_stopped", False))
    elif name == "databricks_command":
        return databricks_command_impl(
            code=arguments.get("code", ""),
            cluster_id=arguments.get("cluster_id"),
            language=arguments.get("language", "python")
        )
    elif name == "create_context":
        return create_context_impl(
            cluster_id=arguments.get("cluster_id"),
            language=arguments.get("language", "python")
        )
    elif name == "execute_command_with_context":
        return execute_command_with_context_impl(
            cluster_id=arguments.get("cluster_id"),
            context_id=arguments.get("context_id"),
            code=arguments.get("code")
        )
    elif name == "destroy_context":
        return destroy_context_impl(
            cluster_id=arguments.get("cluster_id"),
            context_id=arguments.get("context_id")
        )
    elif name == "list_catalogs":
        return list_catalogs_impl()
    elif name == "get_catalog":
        return get_catalog_impl(arguments.get("catalog_name"))
    elif name == "list_schemas":
        return list_schemas_impl(arguments.get("catalog_name"))
    elif name == "get_schema":
        return get_schema_impl(arguments.get("full_schema_name"))
    elif name == "list_tables":
        return list_tables_impl(arguments.get("catalog_name"), arguments.get("schema_name"))
    elif name == "get_table":
        return get_table_impl(arguments.get("full_table_name"))
    elif name == "create_schema":
        return create_schema_impl(
            arguments.get("catalog_name"),
            arguments.get("schema_name"),
            arguments.get("comment")
        )
    elif name == "delete_schema":
        return delete_schema_impl(arguments.get("full_schema_name"))
    elif name == "delete_table":
        return delete_table_impl(arguments.get("full_table_name"))
    else:
        return f"Unknown tool: {name}"


def send_response(response: dict):
    """Send JSON-RPC response to stdout."""
    print(json.dumps(response), flush=True)


def main():
    """Main loop - read JSON-RPC from stdin, write to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        
        method = request.get("method")
        request_id = request.get("id")
        
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "databricks-mcp", "version": "1.0.0"}
                }
            })
        
        elif method == "notifications/initialized":
            # No response needed for notifications
            pass
        
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": TOOLS}
            })
        
        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result_text = handle_tool_call(tool_name, arguments)
            
            send_response({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}]
                }
            })
        
        else:
            # Unknown method
            if request_id:
                send_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}
                })


if __name__ == "__main__":
    main()
