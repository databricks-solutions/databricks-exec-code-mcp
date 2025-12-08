#!/usr/bin/env python3
"""
Databricks Command MCP Server (SSE transport)
Implements the MCP protocol over HTTP with Server-Sent Events
"""
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Databricks Dev MCP (SSE)")

HOST = os.getenv("DATABRICKS_HOST")
TOKEN = os.getenv("DATABRICKS_TOKEN")

if not HOST or not TOKEN:
    raise RuntimeError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


def create_context(cluster_id: str, language: str = "python") -> dict:
    """Create a new execution context on Databricks cluster"""
    try:
        ctx_resp = requests.post(
            f"{HOST}/api/1.2/contexts/create",
            headers=HEADERS,
            json={"clusterId": cluster_id, "language": language}
        )
        ctx_resp.raise_for_status()
        context_id = ctx_resp.json()["id"]

        return {
            "content": [{"type": "text", "text": f"Context created successfully!\n\nContext ID: {context_id}\nCluster ID: {cluster_id}\nLanguage: {language}\n\nUse this context_id for subsequent commands to maintain state."}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error creating context: {str(e)}"}],
            "isError": True
        }


def execute_command_with_context(cluster_id: str, context_id: str, code: str) -> dict:
    """Execute code using an existing context (maintains state between calls)"""
    try:
        # Submit command
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

        # Poll for result
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
                return {
                    "content": [{"type": "text", "text": "Error: Command timed out"}],
                    "isError": True
                }

            time.sleep(2)

        # Return results
        results = status.get("results", {})
        result_type = results.get("resultType", "")

        # Handle errors
        if status.get("status") == "Error" or result_type == "error":
            error_msg = results.get("cause", results.get("summary", "Unknown error"))
            return {
                "content": [{"type": "text", "text": f"Error: {error_msg}"}],
                "isError": True
            }

        # Get the actual result data
        result_data = results.get("data")
        output_text = str(result_data) if result_data else "Success (no output)"

        return {
            "content": [{"type": "text", "text": output_text}]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def destroy_context(cluster_id: str, context_id: str) -> dict:
    """Destroy an execution context"""
    try:
        ctx_resp = requests.post(
            f"{HOST}/api/1.2/contexts/destroy",
            headers=HEADERS,
            json={"clusterId": cluster_id, "contextId": context_id}
        )
        ctx_resp.raise_for_status()

        return {
            "content": [{"type": "text", "text": f"Context {context_id} destroyed successfully!"}]
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error destroying context: {str(e)}"}],
            "isError": True
        }


def execute_databricks_command(cluster_id: str, language: str, code: str) -> dict:
    """Execute code on Databricks cluster (creates and destroys context automatically)"""
    try:
        # 1. Create execution context
        ctx_resp = requests.post(
            f"{HOST}/api/1.2/contexts/create",
            headers=HEADERS,
            json={"clusterId": cluster_id, "language": language}
        )
        ctx_resp.raise_for_status()
        context_id = ctx_resp.json()["id"]

        # 2. Submit command
        cmd_resp = requests.post(
            f"{HOST}/api/1.2/commands/execute",
            headers=HEADERS,
            json={
                "clusterId": cluster_id,
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
                return {
                    "content": [{"type": "text", "text": "Error: Command timed out"}],
                    "isError": True
                }

            time.sleep(2)

        # Return results
        results = status.get("results", {})
        result_type = results.get("resultType", "")

        # Handle errors
        if status.get("status") == "Error" or result_type == "error":
            error_msg = results.get("cause", results.get("summary", "Unknown error"))
            return {
                "content": [{"type": "text", "text": f"Error: {error_msg}"}],
                "isError": True
            }

        # Get the actual result data
        result_data = results.get("data")
        output_text = str(result_data) if result_data else "Success (no output)"

        return {
            "content": [{"type": "text", "text": output_text}]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


# === Unity Catalog REST API Functions ===

def list_catalogs() -> dict:
    """List all catalogs in Unity Catalog"""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/catalogs",
            headers=HEADERS
        )
        resp.raise_for_status()
        data = resp.json()

        catalogs = data.get("catalogs", [])
        output = f"Found {len(catalogs)} catalogs:\n\n"
        for catalog in catalogs:
            output += f"📚 {catalog.get('name')}\n"
            if catalog.get('comment'):
                output += f"   Comment: {catalog.get('comment')}\n"
            output += f"   Owner: {catalog.get('owner')}\n"
            output += f"   Created: {catalog.get('created_at')}\n\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def get_catalog(catalog_name: str) -> dict:
    """Get detailed information about a specific catalog"""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/catalogs/{catalog_name}",
            headers=HEADERS
        )
        resp.raise_for_status()
        catalog = resp.json()

        output = f"📚 Catalog: {catalog.get('name')}\n"
        output += f"   Full Name: {catalog.get('full_name')}\n"
        output += f"   Owner: {catalog.get('owner')}\n"
        output += f"   Comment: {catalog.get('comment', 'N/A')}\n"
        output += f"   Created: {catalog.get('created_at')}\n"
        output += f"   Updated: {catalog.get('updated_at')}\n"
        output += f"   Storage Location: {catalog.get('storage_location', 'N/A')}\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def list_schemas(catalog_name: str) -> dict:
    """List all schemas in a catalog"""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/schemas",
            headers=HEADERS,
            params={"catalog_name": catalog_name}
        )
        resp.raise_for_status()
        data = resp.json()

        schemas = data.get("schemas", [])
        output = f"Found {len(schemas)} schemas in catalog '{catalog_name}':\n\n"
        for schema in schemas:
            output += f"📁 {schema.get('name')}\n"
            if schema.get('comment'):
                output += f"   Comment: {schema.get('comment')}\n"
            output += f"   Owner: {schema.get('owner')}\n"
            output += f"   Full Name: {schema.get('full_name')}\n\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def get_schema(full_schema_name: str) -> dict:
    """Get detailed information about a specific schema"""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/schemas/{full_schema_name}",
            headers=HEADERS
        )
        resp.raise_for_status()
        schema = resp.json()

        output = f"📁 Schema: {schema.get('name')}\n"
        output += f"   Full Name: {schema.get('full_name')}\n"
        output += f"   Catalog: {schema.get('catalog_name')}\n"
        output += f"   Owner: {schema.get('owner')}\n"
        output += f"   Comment: {schema.get('comment', 'N/A')}\n"
        output += f"   Created: {schema.get('created_at')}\n"
        output += f"   Updated: {schema.get('updated_at')}\n"
        output += f"   Storage Location: {schema.get('storage_location', 'N/A')}\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def list_tables(catalog_name: str, schema_name: str) -> dict:
    """List all tables in a schema"""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/tables",
            headers=HEADERS,
            params={
                "catalog_name": catalog_name,
                "schema_name": schema_name
            }
        )
        resp.raise_for_status()
        data = resp.json()

        tables = data.get("tables", [])
        output = f"Found {len(tables)} tables in {catalog_name}.{schema_name}:\n\n"
        for table in tables:
            output += f"📊 {table.get('name')}\n"
            output += f"   Type: {table.get('table_type')}\n"
            if table.get('comment'):
                output += f"   Comment: {table.get('comment')}\n"
            output += f"   Owner: {table.get('owner')}\n"
            output += f"   Full Name: {table.get('full_name')}\n\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def get_table(full_table_name: str) -> dict:
    """Get detailed information about a specific table"""
    try:
        resp = requests.get(
            f"{HOST}/api/2.1/unity-catalog/tables/{full_table_name}",
            headers=HEADERS
        )
        resp.raise_for_status()
        table = resp.json()

        output = f"📊 Table: {table.get('name')}\n"
        output += f"   Full Name: {table.get('full_name')}\n"
        output += f"   Catalog: {table.get('catalog_name')}\n"
        output += f"   Schema: {table.get('schema_name')}\n"
        output += f"   Type: {table.get('table_type')}\n"
        output += f"   Owner: {table.get('owner')}\n"
        output += f"   Comment: {table.get('comment', 'N/A')}\n"
        output += f"   Created: {table.get('created_at')}\n"
        output += f"   Updated: {table.get('updated_at')}\n"
        output += f"   Storage Location: {table.get('storage_location', 'N/A')}\n"

        # Add column information
        columns = table.get('columns', [])
        if columns:
            output += f"\n   Columns ({len(columns)}):\n"
            for col in columns:
                output += f"     - {col.get('name')}: {col.get('type_name')}\n"
                if col.get('comment'):
                    output += f"       {col.get('comment')}\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


# === Unity Catalog WRITE Operations ===

def create_schema(catalog_name: str, schema_name: str, comment: str = None) -> dict:
    """Create a new schema in Unity Catalog"""
    try:
        payload = {
            "name": schema_name,
            "catalog_name": catalog_name
        }
        if comment:
            payload["comment"] = comment

        resp = requests.post(
            f"{HOST}/api/2.1/unity-catalog/schemas",
            headers=HEADERS,
            json=payload
        )
        resp.raise_for_status()
        schema = resp.json()

        output = f"✅ Schema created successfully!\n\n"
        output += f"📁 Schema: {schema.get('name')}\n"
        output += f"   Full Name: {schema.get('full_name')}\n"
        output += f"   Catalog: {schema.get('catalog_name')}\n"
        output += f"   Owner: {schema.get('owner')}\n"
        if schema.get('comment'):
            output += f"   Comment: {schema.get('comment')}\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error creating schema: {str(e)}"}],
            "isError": True
        }


def update_schema(full_schema_name: str, new_name: str = None, comment: str = None, owner: str = None) -> dict:
    """Update an existing schema in Unity Catalog"""
    try:
        payload = {}
        if new_name:
            payload["new_name"] = new_name
        if comment:
            payload["comment"] = comment
        if owner:
            payload["owner"] = owner

        if not payload:
            return {
                "content": [{"type": "text", "text": "Error: At least one field (new_name, comment, or owner) must be provided"}],
                "isError": True
            }

        resp = requests.patch(
            f"{HOST}/api/2.1/unity-catalog/schemas/{full_schema_name}",
            headers=HEADERS,
            json=payload
        )
        resp.raise_for_status()
        schema = resp.json()

        output = f"✅ Schema updated successfully!\n\n"
        output += f"📁 Schema: {schema.get('name')}\n"
        output += f"   Full Name: {schema.get('full_name')}\n"
        output += f"   Owner: {schema.get('owner')}\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error updating schema: {str(e)}"}],
            "isError": True
        }


def delete_schema(full_schema_name: str) -> dict:
    """Delete a schema from Unity Catalog"""
    try:
        resp = requests.delete(
            f"{HOST}/api/2.1/unity-catalog/schemas/{full_schema_name}",
            headers=HEADERS
        )
        resp.raise_for_status()

        output = f"✅ Schema '{full_schema_name}' deleted successfully!"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error deleting schema: {str(e)}"}],
            "isError": True
        }


def create_table(catalog_name: str, schema_name: str, table_name: str,
                 columns: list, table_type: str = "MANAGED",
                 comment: str = None, storage_location: str = None) -> dict:
    """Create a new table in Unity Catalog"""
    try:
        payload = {
            "name": table_name,
            "catalog_name": catalog_name,
            "schema_name": schema_name,
            "table_type": table_type,
            "columns": columns,
            "data_source_format": "DELTA"
        }

        if comment:
            payload["comment"] = comment

        if storage_location and table_type == "EXTERNAL":
            payload["storage_location"] = storage_location

        resp = requests.post(
            f"{HOST}/api/2.1/unity-catalog/tables",
            headers=HEADERS,
            json=payload
        )
        resp.raise_for_status()
        table = resp.json()

        output = f"✅ Table created successfully!\n\n"
        output += f"📊 Table: {table.get('name')}\n"
        output += f"   Full Name: {table.get('full_name')}\n"
        output += f"   Catalog: {table.get('catalog_name')}\n"
        output += f"   Schema: {table.get('schema_name')}\n"
        output += f"   Type: {table.get('table_type')}\n"
        output += f"   Owner: {table.get('owner')}\n"
        if table.get('comment'):
            output += f"   Comment: {table.get('comment')}\n"

        # Show columns
        created_columns = table.get('columns', [])
        if created_columns:
            output += f"\n   Columns ({len(created_columns)}):\n"
            for col in created_columns:
                output += f"     - {col.get('name')}: {col.get('type_name')}\n"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error creating table: {str(e)}"}],
            "isError": True
        }


def delete_table(full_table_name: str) -> dict:
    """Delete a table from Unity Catalog"""
    try:
        resp = requests.delete(
            f"{HOST}/api/2.1/unity-catalog/tables/{full_table_name}",
            headers=HEADERS
        )
        resp.raise_for_status()

        output = f"✅ Table '{full_table_name}' deleted successfully!"

        return {"content": [{"type": "text", "text": output}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error deleting table: {str(e)}"}],
            "isError": True
        }


@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint for MCP communication"""
    async def event_generator():
        # Send endpoint event
        endpoint_event = {
            "jsonrpc": "2.0",
            "method": "endpoint",
            "params": {
                "endpoint": "/message"
            }
        }
        yield f"data: {json.dumps(endpoint_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/message")
async def message_endpoint(request: Request):
    """Handle MCP JSON-RPC messages"""
    try:
        request_data = await request.json()
        method = request_data.get("method")

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "databricks-dev-mcp",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "create_context",
                            "description": "Create a new execution context on Databricks cluster. Returns a context_id that can be used for subsequent commands to maintain state (variables, imports, etc) between calls.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "cluster_id": {
                                        "type": "string",
                                        "description": "Databricks cluster ID"
                                    },
                                    "language": {
                                        "type": "string",
                                        "description": "Language (python, scala, sql, r)",
                                        "default": "python"
                                    }
                                },
                                "required": ["cluster_id"]
                            }
                        },
                        {
                            "name": "execute_command_with_context",
                            "description": "Execute code using an existing context. This maintains state between calls - variables, imports, and data persist across commands. Use create_context first to get a context_id.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "cluster_id": {
                                        "type": "string",
                                        "description": "Databricks cluster ID"
                                    },
                                    "context_id": {
                                        "type": "string",
                                        "description": "Context ID from create_context"
                                    },
                                    "code": {
                                        "type": "string",
                                        "description": "Python code to execute"
                                    }
                                },
                                "required": ["cluster_id", "context_id", "code"]
                            }
                        },
                        {
                            "name": "destroy_context",
                            "description": "Destroy an execution context to free resources. Call this when you're done with a context.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "cluster_id": {
                                        "type": "string",
                                        "description": "Databricks cluster ID"
                                    },
                                    "context_id": {
                                        "type": "string",
                                        "description": "Context ID to destroy"
                                    }
                                },
                                "required": ["cluster_id", "context_id"]
                            }
                        },
                        {
                            "name": "databricks_command",
                            "description": "Executes Python code on a Databricks cluster via the Command Execution API (creates and destroys context automatically - does NOT maintain state between calls)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "cluster_id": {
                                        "type": "string",
                                        "description": "Databricks cluster ID"
                                    },
                                    "language": {
                                        "type": "string",
                                        "description": "Language (python, scala, etc)",
                                        "default": "python"
                                    },
                                    "code": {
                                        "type": "string",
                                        "description": "Code to execute"
                                    }
                                },
                                "required": ["cluster_id", "language", "code"]
                            }
                        },
                        {
                            "name": "list_catalogs",
                            "description": "List all catalogs in Unity Catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_catalog",
                            "description": "Get detailed information about a specific catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "catalog_name": {
                                        "type": "string",
                                        "description": "Name of the catalog"
                                    }
                                },
                                "required": ["catalog_name"]
                            }
                        },
                        {
                            "name": "list_schemas",
                            "description": "List all schemas in a catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "catalog_name": {
                                        "type": "string",
                                        "description": "Name of the catalog"
                                    }
                                },
                                "required": ["catalog_name"]
                            }
                        },
                        {
                            "name": "get_schema",
                            "description": "Get detailed information about a specific schema",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "full_schema_name": {
                                        "type": "string",
                                        "description": "Full schema name (catalog.schema)"
                                    }
                                },
                                "required": ["full_schema_name"]
                            }
                        },
                        {
                            "name": "list_tables",
                            "description": "List all tables in a schema",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "catalog_name": {
                                        "type": "string",
                                        "description": "Name of the catalog"
                                    },
                                    "schema_name": {
                                        "type": "string",
                                        "description": "Name of the schema"
                                    }
                                },
                                "required": ["catalog_name", "schema_name"]
                            }
                        },
                        {
                            "name": "get_table",
                            "description": "Get detailed information about a specific table including columns",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "full_table_name": {
                                        "type": "string",
                                        "description": "Full table name (catalog.schema.table)"
                                    }
                                },
                                "required": ["full_table_name"]
                            }
                        },
                        {
                            "name": "create_table",
                            "description": "Create a new table in Unity Catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "catalog_name": {
                                        "type": "string",
                                        "description": "Name of the catalog"
                                    },
                                    "schema_name": {
                                        "type": "string",
                                        "description": "Name of the schema"
                                    },
                                    "table_name": {
                                        "type": "string",
                                        "description": "Name of the table to create"
                                    },
                                    "columns": {
                                        "type": "array",
                                        "description": "Array of column definitions. Each column should have 'name', 'type_name', and optional 'comment'. Example: [{'name': 'id', 'type_name': 'INT', 'comment': 'Primary key'}, {'name': 'name', 'type_name': 'STRING'}]",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {
                                                    "type": "string",
                                                    "description": "Column name"
                                                },
                                                "type_name": {
                                                    "type": "string",
                                                    "description": "Column data type (e.g., INT, STRING, DOUBLE, TIMESTAMP, etc.)"
                                                },
                                                "comment": {
                                                    "type": "string",
                                                    "description": "Optional column description"
                                                }
                                            },
                                            "required": ["name", "type_name"]
                                        }
                                    },
                                    "table_type": {
                                        "type": "string",
                                        "description": "Table type: MANAGED or EXTERNAL (default: MANAGED)",
                                        "default": "MANAGED"
                                    },
                                    "comment": {
                                        "type": "string",
                                        "description": "Optional comment describing the table"
                                    },
                                    "storage_location": {
                                        "type": "string",
                                        "description": "Storage location (required for EXTERNAL tables)"
                                    }
                                },
                                "required": ["catalog_name", "schema_name", "table_name", "columns"]
                            }
                        },
                        {
                            "name": "create_schema",
                            "description": "Create a new schema in Unity Catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "catalog_name": {
                                        "type": "string",
                                        "description": "Name of the catalog"
                                    },
                                    "schema_name": {
                                        "type": "string",
                                        "description": "Name of the schema to create"
                                    },
                                    "comment": {
                                        "type": "string",
                                        "description": "Optional comment describing the schema"
                                    }
                                },
                                "required": ["catalog_name", "schema_name"]
                            }
                        },
                        {
                            "name": "update_schema",
                            "description": "Update an existing schema in Unity Catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "full_schema_name": {
                                        "type": "string",
                                        "description": "Full schema name (catalog.schema)"
                                    },
                                    "new_name": {
                                        "type": "string",
                                        "description": "Optional new name for the schema"
                                    },
                                    "comment": {
                                        "type": "string",
                                        "description": "Optional new comment"
                                    },
                                    "owner": {
                                        "type": "string",
                                        "description": "Optional new owner"
                                    }
                                },
                                "required": ["full_schema_name"]
                            }
                        },
                        {
                            "name": "delete_schema",
                            "description": "Delete a schema from Unity Catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "full_schema_name": {
                                        "type": "string",
                                        "description": "Full schema name (catalog.schema)"
                                    }
                                },
                                "required": ["full_schema_name"]
                            }
                        },
                        {
                            "name": "delete_table",
                            "description": "Delete a table from Unity Catalog",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "full_table_name": {
                                        "type": "string",
                                        "description": "Full table name (catalog.schema.table)"
                                    }
                                },
                                "required": ["full_table_name"]
                            }
                        }
                    ]
                }
            }

        elif method == "tools/call":
            params = request_data.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "create_context":
                result = create_context(
                    arguments.get("cluster_id"),
                    arguments.get("language", "python")
                )
            elif tool_name == "execute_command_with_context":
                result = execute_command_with_context(
                    arguments.get("cluster_id"),
                    arguments.get("context_id"),
                    arguments.get("code")
                )
            elif tool_name == "destroy_context":
                result = destroy_context(
                    arguments.get("cluster_id"),
                    arguments.get("context_id")
                )
            elif tool_name == "databricks_command":
                result = execute_databricks_command(
                    arguments.get("cluster_id"),
                    arguments.get("language", "python"),
                    arguments.get("code")
                )
            elif tool_name == "list_catalogs":
                result = list_catalogs()
            elif tool_name == "get_catalog":
                result = get_catalog(arguments.get("catalog_name"))
            elif tool_name == "list_schemas":
                result = list_schemas(arguments.get("catalog_name"))
            elif tool_name == "get_schema":
                result = get_schema(arguments.get("full_schema_name"))
            elif tool_name == "list_tables":
                result = list_tables(
                    arguments.get("catalog_name"),
                    arguments.get("schema_name")
                )
            elif tool_name == "get_table":
                result = get_table(arguments.get("full_table_name"))
            elif tool_name == "create_table":
                result = create_table(
                    arguments.get("catalog_name"),
                    arguments.get("schema_name"),
                    arguments.get("table_name"),
                    arguments.get("columns"),
                    arguments.get("table_type", "MANAGED"),
                    arguments.get("comment"),
                    arguments.get("storage_location")
                )
            elif tool_name == "create_schema":
                result = create_schema(
                    arguments.get("catalog_name"),
                    arguments.get("schema_name"),
                    arguments.get("comment")
                )
            elif tool_name == "update_schema":
                result = update_schema(
                    arguments.get("full_schema_name"),
                    arguments.get("new_name"),
                    arguments.get("comment"),
                    arguments.get("owner")
                )
            elif tool_name == "delete_schema":
                result = delete_schema(arguments.get("full_schema_name"))
            elif tool_name == "delete_table":
                result = delete_table(arguments.get("full_table_name"))
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_data.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
                return response

            response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "result": result
            }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }

        return response

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if 'request_data' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


@app.get("/")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "transport": "sse"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
