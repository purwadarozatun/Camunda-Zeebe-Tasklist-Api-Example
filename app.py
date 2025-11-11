import os
import sys
import json
from typing import Any, Dict, Optional, AsyncGenerator, List
from contextlib import asynccontextmanager

# Add current directory to path for proto imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import httpx

from pyzeebe import ZeebeClient, create_insecure_channel, create_camunda_cloud_channel

# User Task gRPC implementation using custom proto files
import grpc
from proto.user_task_pb2 import (
    CompleteUserTaskRequest,
    AssignUserTaskRequest,
    UnassignUserTaskRequest,
    GetUserTaskRequest,
    UserTaskState,
)
from proto.user_task_pb2_grpc import UserTaskGatewayStub

load_dotenv()

# ====== ENV ======
ZEEBE_ADDRESS = os.getenv("ZEEBE_ADDRESS", "localhost:26500")
ZEEBE_CLIENT_ID = os.getenv("ZEEBE_CLIENT_ID")
ZEEBE_CLIENT_SECRET = os.getenv("ZEEBE_CLIENT_SECRET")
ZEEBE_AUTHORIZATION_SERVER_URL = os.getenv("ZEEBE_AUTHORIZATION_SERVER_URL")
ZEEBE_AUDIENCE = os.getenv("ZEEBE_AUDIENCE")
ZEEBE_CLUSTER_ID = os.getenv("ZEEBE_CLUSTER_ID")

# Camunda REST API configuration
CAMUNDA_REST_URL = os.getenv("CAMUNDA_REST_URL", "http://localhost:8080").rstrip("/")
CAMUNDA_REST_CLIENT_ID = os.getenv("CAMUNDA_REST_CLIENT_ID", ZEEBE_CLIENT_ID)
CAMUNDA_REST_CLIENT_SECRET = os.getenv("CAMUNDA_REST_CLIENT_SECRET", ZEEBE_CLIENT_SECRET)
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"  # Enable mock mode for testing

# ES config - DEPRECATED (removed ES implementation)
# ES_URL = os.getenv("ES_URL", "http://localhost:9200").rstrip("/")
# ES_USER = os.getenv("ES_USER", "")
# ES_PASS = os.getenv("ES_PASS", "")

# CORS
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

zeebe_client: Optional[ZeebeClient] = None

# Constants
USER_TASK_NOT_SUPPORTED_MSG = (
    "User Task operations are not supported in pyzeebe 4.7.0. "
    "Please use Camunda 8 REST API or implement direct gRPC calls with proper proto definitions."
)

USER_TASK_GRPC_ERROR_MSG = "User Task gRPC API not available in current Zeebe version"
USER_TASK_REST_SUGGESTION = "Use Camunda 8 REST API instead"
TASKLIST_API_SUGGESTION = "Check if Tasklist API is running and accessible"


def _make_user_task_grpc_stub(address: str) -> UserTaskGatewayStub:
    """Create gRPC stub for User Task operations."""
    channel = grpc.insecure_channel(address)
    return UserTaskGatewayStub(channel)


async def get_camunda_auth_token() -> Optional[str]:
    """Get authentication token for Camunda REST API."""
    if not CAMUNDA_REST_CLIENT_ID or not CAMUNDA_REST_CLIENT_SECRET:
        return None
    
    try:
        auth_url = ZEEBE_AUTHORIZATION_SERVER_URL or "http://localhost:8080/auth/realms/camunda-platform/protocol/openid-connect/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                auth_url,
                data={
                    "client_id": CAMUNDA_REST_CLIENT_ID,
                    "client_secret": CAMUNDA_REST_CLIENT_SECRET,
                    "audience": "camunda-identity",
                    "grant_type": "client_credentials"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                print(f"Failed to get auth token: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        print(f"Auth error: {e}")
        return None


async def camunda_api_call(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make API call to Camunda REST API."""
    token = await get_camunda_auth_token()
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"{CAMUNDA_REST_URL}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method.upper() == "PATCH":
            response = await client.patch(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return {"ok": True}
            
        return response.json()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global zeebe_client
    print("🚀 Init Zeebe client...")
    if (ZEEBE_CLIENT_ID and ZEEBE_CLIENT_SECRET and
        ZEEBE_AUTHORIZATION_SERVER_URL and ZEEBE_AUDIENCE):
        channel = create_camunda_cloud_channel(
            client_id=ZEEBE_CLIENT_ID,
            client_secret=ZEEBE_CLIENT_SECRET,
            auth_server_url=ZEEBE_AUTHORIZATION_SERVER_URL,
            audience=ZEEBE_AUDIENCE,
            gateway_address=ZEEBE_ADDRESS if ZEEBE_ADDRESS else None,
            cluster_id=ZEEBE_CLUSTER_ID if ZEEBE_CLUSTER_ID else None,
        )
        print("✅ SaaS connected")
    else:
        channel = create_insecure_channel(ZEEBE_ADDRESS)  # pyzeebe 3.0.0: positional "host:port"
        print(f"✅ Local connected {ZEEBE_ADDRESS}")

    zeebe_client = ZeebeClient(channel)
    try:
        topo = await zeebe_client.topology()  # sanity check
        print("🔎 Topology:", topo)
    except Exception as e:
        print("⚠️ Topology check failed:", e)

    yield
    print("🧹 Shutdown.")


app = FastAPI(title="Camunda 8 – FastAPI RPC + ES Task List", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if CORS_ORIGINS == ["*"] else CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="public"), name="static")


# ====== Schemas ======
class StartBody(BaseModel):
    bpmnProcessId: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[int] = None  # -1 latest jika None

class MessageBody(BaseModel):
    messageName: str
    correlationKey: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    timeToLive: int = 60000

class CancelBody(BaseModel):
    processInstanceKey: int

class DeployBody(BaseModel):
    bpmnPath: str

class CompleteUserTaskBody(BaseModel):
    userTaskKey: int
    variables: Dict[str, Any] = Field(default_factory=dict)

class AssignBody(BaseModel):
    userTaskKey: int
    assignee: str
    allowOverride: bool = True

class UnassignBody(BaseModel):
    userTaskKey: int


# ====== Removed ES utility - now using Camunda REST API v2 ======


# ====== Web Routes ======
@app.get("/")
async def home():
    """Serve the main HTML dashboard."""
    return FileResponse("public/probis-zeebe-proxy.html")

@app.get("/dashboard")
async def dashboard():
    """Alternative endpoint for the dashboard."""
    return FileResponse("public/probis-zeebe-proxy.html")

# ====== RPC Routes ======
@app.get("/rpc/health")
async def health():
    try:
        topo = await zeebe_client.topology()  # type: ignore
        return {"ok": True, "topology": topo}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post("/rpc/start")
async def start_process(body: StartBody):
    try:
        version = body.version if body.version is not None else -1
        resp = await zeebe_client.run_process(  # type: ignore
            bpmn_process_id=body.bpmnProcessId,
            variables=body.variables,
            version=version,
        )
        return {"ok": True, "processInstanceKey": resp.process_instance_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rpc/start-with-file")
async def start_process_with_file(
    bpmn_process_id: str = Form(..., description="BPMN Process ID", alias="bpmnProcessId"),
    variables: str = Form("{}", description="Process variables as JSON string"),
    version: Optional[int] = Form(None, description="Process version"),
    file: Optional[UploadFile] = File(None, description="Optional file attachment")
):
    """Start process instance with optional file attachment."""
    try:
        print(f"DEBUG: Received request - process_id: {bpmn_process_id}, variables: {variables}")
        print(f"DEBUG: File: {file.filename if file else 'No file'}")
        # Parse variables JSON
        try:
            process_variables = json.loads(variables)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in variables field")
        
        # Handle file upload if provided
        if file and file.filename:
            # Create uploads directory if not exists
            uploads_dir = "uploads/attachments"
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save uploaded file with unique name
            import time
            timestamp = str(int(time.time()))
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(uploads_dir, unique_filename)
            
            # Save file content
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Add file info to process variables
            process_variables.update({
                "attachedFile": {
                    "filename": file.filename,
                    "uniqueName": unique_filename,
                    "path": file_path,
                    "size": len(content),
                    "contentType": file.content_type,
                    "uploadTimestamp": timestamp
                }
            })
        
        # Start process
        process_version = version if version is not None else -1
        resp = await zeebe_client.run_process(  # type: ignore
            bpmn_process_id=bpmn_process_id,
            variables=process_variables,
            version=process_version,
        )
        
        return {
            "ok": True,
            "processInstanceKey": resp.process_instance_key,
            "bpmnProcessId": bpmn_process_id,
            "version": process_version,
            "fileAttached": file.filename if file and file.filename else None,
            "variables": process_variables
        }
        
    except Exception as e:
        # Clean up file if process start fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail={
            "error": "Failed to start process with file",
            "details": str(e),
            "filename": file.filename if file and file.filename else None
        })


@app.post("/rpc/message")
async def publish_message(body: MessageBody):
    try:
        await zeebe_client.publish_message(  # type: ignore
            name=body.messageName,
            correlation_key=str(body.correlationKey),
            time_to_live=body.timeToLive,
            variables=body.variables,
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rpc/cancel")
async def cancel_instance(body: CancelBody):
    try:
        await zeebe_client.cancel_process_instance(  # type: ignore
            process_instance_key=body.processInstanceKey
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rpc/deploy")
async def deploy_process(body: DeployBody):
    try:
        # In pyzeebe 4.7.0, deploy_process was renamed to deploy_resource
        await zeebe_client.deploy_resource(body.bpmnPath)  # type: ignore
        return {"ok": True, "deployed": body.bpmnPath}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rpc/deploy-upload")
async def deploy_uploaded_bpmn(
    file: UploadFile = File(..., description="BPMN file to upload and deploy"),
    process_name: Optional[str] = Form(None, description="Optional process name")
):
    """Upload and deploy BPMN file to Zeebe."""
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(('.bpmn', '.bpmn20.xml')):
            raise HTTPException(
                status_code=400, 
                detail="File must be a BPMN file (.bpmn or .bpmn20.xml)"
            )
        
        # Create uploads directory if not exists
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save uploaded file
        file_path = os.path.join(uploads_dir, file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Deploy to Zeebe
        result = await zeebe_client.deploy_resource(file_path)  # type: ignore
        
        # Extract deployment info
        processes = []
        if hasattr(result, 'processes'):
            for process in result.processes:
                processes.append({
                    "bpmnProcessId": process.bpmn_process_id,
                    "version": process.version,
                    "processDefinitionKey": process.process_definition_key,
                    "resourceName": process.resource_name
                })
        
        return {
            "ok": True,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": len(content),
            "deployment_key": result.key if hasattr(result, 'key') else None,
            "processes": processes
        }
        
    except Exception as e:
        # Clean up file if deployment fails
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail={
            "error": "Failed to deploy uploaded BPMN",
            "details": str(e),
            "filename": file.filename if file and file.filename else "unknown"
        })


# ====== User Task: complete / assign / unassign ======
@app.post("/rpc/user-task/complete")
async def rpc_complete_user_task(body: CompleteUserTaskBody):
    """Complete a user task using Camunda REST API v2."""
    try:
        endpoint = f"/v2/user-tasks/{body.userTaskKey}/completion"
        data = {
            "variables": body.variables or {}
        }
        
        result = await camunda_api_call("POST", endpoint, data)
        return {"ok": True, "result": result}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail={
                "error": "User task not found",
                "taskKey": body.userTaskKey,
                "suggestion": "Check if the task key is correct and the task still exists"
            })
        raise HTTPException(status_code=e.response.status_code, detail={
            "error": f"Camunda REST API error: {e.response.status_code}",
            "details": e.response.text,
            "endpoint": endpoint
        })
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail={
            "error": "Cannot connect to Camunda REST API",
            "camunda_url": CAMUNDA_REST_URL,
            "suggestion": "Make sure Camunda 8 is running on " + CAMUNDA_REST_URL
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Failed to complete user task",
            "details": str(e),
            "suggestion": TASKLIST_API_SUGGESTION
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Failed to complete user task",
            "details": str(e),
            "suggestion": TASKLIST_API_SUGGESTION
        })


@app.post("/rpc/user-task/assign")
async def rpc_assign_user_task(body: AssignBody):
    """Assign a user task using Camunda REST API v2."""
    try:
        endpoint = f"/v2/user-tasks/{body.userTaskKey}/assignment"
        data = {
            "assignee": body.assignee,
            "allowOverride": body.allowOverride
        }
        
        result = await camunda_api_call("POST", endpoint, data)
        return {"ok": True, "result": result}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail={
                "error": "User task not found",
                "taskKey": body.userTaskKey
            })
        raise HTTPException(status_code=e.response.status_code, detail={
            "error": f"Camunda REST API error: {e.response.status_code}",
            "details": e.response.text,
            "endpoint": endpoint
        })
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail={
            "error": "Cannot connect to Camunda REST API",
            "camunda_url": CAMUNDA_REST_URL,
            "suggestion": "Make sure Camunda 8 is running on " + CAMUNDA_REST_URL
        })


@app.post("/rpc/user-task/unassign")
async def rpc_unassign_user_task(body: UnassignBody):
    """Unassign a user task using Camunda REST API v2."""
    try:
        endpoint = f"/v2/user-tasks/{body.userTaskKey}/assignee"
        
        result = await camunda_api_call("DELETE", endpoint)
        return {"ok": True, "result": result}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail={
            "error": f"Camunda REST API error: {e.response.status_code}",
            "details": e.response.text,
            "endpoint": endpoint
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Failed to unassign user task",
            "details": str(e),
            "suggestion": TASKLIST_API_SUGGESTION
        })


# ====== Redirect old /rpc/tasks to new v2 implementation ======
@app.get("/rpc/tasks")
async def list_tasks(assignee: str = Query(..., description="Username assignee")):
    """Redirect to Camunda REST API v2 implementation."""
    # Call v2 directly without passing Query objects
    return await list_tasks_v2(assignee=assignee, state="CREATED", page_size=50)


# Get user tasks using Camunda REST API v2
@app.get("/rpc/tasks-v2")
async def list_tasks_v2(
    assignee: Optional[str] = Query(None, description="Filter by assignee"),
    state: Optional[str] = Query("CREATED", description="Task state (CREATED, COMPLETED, CANCELED)"),
    page_size: int = Query(50, description="Number of tasks per page")
):
    """List user tasks using Camunda REST API v2."""
    try:
        endpoint = "/v2/user-tasks/search"
        
        # Build search query
        search_query = {
            "page": {"limit": page_size}
        }
        
        # Add filters - Camunda REST API v2 format
        if state or assignee:
            search_query["filter"] = {}
            if state:
                search_query["filter"]["state"] = state
            if assignee:
                search_query["filter"]["assignee"] = assignee
        
        result = await camunda_api_call("POST", endpoint, search_query)
        
        # Format response to match existing structure  
        tasks = []
        for task in result.get("items", []):
            tasks.append({
                "userTaskKey": task.get("userTaskKey"),
                "taskName": task.get("elementId"),
                "assignee": task.get("assignee"),
                "processInstanceKey": task.get("processInstanceKey"),
                "state": task.get("state"),
                "creationDate": task.get("creationDate"),
                "formKey": task.get("formKey"),
                "processDefinitionKey": task.get("processDefinitionKey")
            })
        
        return {
            "ok": True,
            "count": len(tasks),
            "tasks": tasks,
            "totalCount": result.get("totalCount", len(tasks))
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail={
            "error": f"Camunda REST API error: {e.response.status_code}",
            "details": e.response.text,
            "endpoint": endpoint
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Failed to list tasks",
            "details": str(e),
            "suggestion": TASKLIST_API_SUGGESTION
        })


# Extra: get ONE user task by key via Camunda REST API v2
@app.get("/rpc/user-task/{key}")
async def get_user_task(key: str):
    """Get user task details using Camunda REST API v2."""
    try:
        endpoint = f"/v2/user-tasks/{key}"
        
        result = await camunda_api_call("GET", endpoint)
        
        # Format response
        task_data = {
            "userTaskKey": result.get("userTaskKey"),
            "taskName": result.get("elementId"),
            "assignee": result.get("assignee"),
            "processInstanceKey": result.get("processInstanceKey"),
            "state": result.get("state"),
            "creationDate": result.get("creationDate"),
            "completionDate": result.get("completionDate"),
            "formKey": result.get("formKey"),
            "processDefinitionKey": result.get("processDefinitionKey"),
            "variables": result.get("variables", {})
        }
        
        return {"ok": True, "task": task_data}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail={
                "error": "User task not found",
                "taskKey": key
            })
        raise HTTPException(status_code=e.response.status_code, detail={
            "error": f"Camunda REST API error: {e.response.status_code}",
            "details": e.response.text,
            "endpoint": endpoint
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Failed to get user task",
            "details": str(e),
            "suggestion": TASKLIST_API_SUGGESTION
        })


async def get_process_variables(process_instance_key: str):
    """Get process variables from Camunda REST API v2."""
    try:
        endpoint = "/v2/variables/search"
        payload = {
            "filter": {
                "processInstanceKey": {"$eq": process_instance_key},
                "scopeKey": {"$eq": process_instance_key}
            },
            "page": {"from": 0, "limit": 50},
            "sort": [{"field": "name", "order": "asc"}]
        }
        
        result = await camunda_api_call("POST", endpoint, data=payload)
        return result.get("items", [])
    except Exception as e:
        print(f"Failed to get process variables: {e}")
        return []

@app.get("/rpc/user-task/{key}/pretty")
async def get_user_task_pretty(key: str):
    """Get user task details in pretty JSON format with process variables."""
    try:
        endpoint = f"/v2/user-tasks/{key}"
        
        result = await camunda_api_call("GET", endpoint)
        
        # Get process variables from the dedicated endpoint
        process_instance_key = result.get("processInstanceKey")
        process_variables = []
        if process_instance_key:
            process_variables = await get_process_variables(str(process_instance_key))
        
        # Combine task variables and process variables
        task_variables = result.get("variables", {})
        
        # Create comprehensive variables dict from process variables
        all_variables = {}
        for var_item in process_variables:
            var_name = var_item.get("name", "")
            all_variables[var_name] = {
                "value": var_item.get("value"),
                "type": var_item.get("type", "unknown"),
                "scope": var_item.get("scopeKey"),
                "processInstanceKey": var_item.get("processInstanceKey"),
                "source": "process_instance"
            }
        
        # Add task-level variables (if any)
        for var_name, var_data in task_variables.items():
            if var_name not in all_variables:
                if isinstance(var_data, dict):
                    all_variables[var_name] = {
                        "value": var_data.get("value"),
                        "type": var_data.get("type", "unknown"),
                        "scope": "task",
                        "processInstanceKey": process_instance_key,
                        "source": "task_level"
                    }
                else:
                    all_variables[var_name] = {
                        "value": var_data,
                        "type": "direct",
                        "scope": "task",
                        "processInstanceKey": process_instance_key,
                        "source": "task_level"
                    }
        
        # Process variables for summary
        processed_variables = {}
        variable_summary = {
            "count": len(all_variables),
            "sources": {"process_instance": 0, "task_level": 0},
            "types": {},
            "names": list(all_variables.keys())
        }
        
        # Process each variable for detailed info
        for var_name, var_data in all_variables.items():
            var_value = var_data.get("value")
            var_type = var_data.get("type", "unknown")
            var_source = var_data.get("source", "unknown")
            
            processed_variables[var_name] = {
                "value": var_value,
                "type": var_type,
                "source": var_source,
                "scope": var_data.get("scope"),
                "processInstanceKey": var_data.get("processInstanceKey"),
                "raw": var_data
            }
            
            # Count variable sources
            if var_source in variable_summary["sources"]:
                variable_summary["sources"][var_source] += 1
            else:
                variable_summary["sources"][var_source] = 1
            
            # Count variable types
            if var_type in variable_summary["types"]:
                variable_summary["types"][var_type] += 1
            else:
                variable_summary["types"][var_type] = 1

        # Return full response with pretty formatting
        response_data = {
            "ok": True,
            "taskKey": key,
            "taskDetails": result,
            "formatted": {
                "userTaskKey": result.get("userTaskKey"),
                "taskName": result.get("elementId"),
                "assignee": result.get("assignee"),
                "processInstanceKey": result.get("processInstanceKey"),
                "state": result.get("state"),
                "creationDate": result.get("creationDate"),
                "completionDate": result.get("completionDate"),
                "formKey": result.get("formKey"),
                "processDefinitionKey": result.get("processDefinitionKey"),
                "variables": {
                    "summary": variable_summary,
                    "data": processed_variables,
                    "processVariables": process_variables,
                    "taskVariables": task_variables
                }
            }
        }
        
        # Return pretty formatted JSON
        return Response(
            content=json.dumps(response_data, indent=2, ensure_ascii=False),
            media_type="application/json"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error_data = {
                "ok": False,
                "error": "User task not found",
                "taskKey": key,
                "suggestion": "Check if the task key is correct and the task still exists"
            }
            return Response(
                content=json.dumps(error_data, indent=2, ensure_ascii=False),
                status_code=404,
                media_type="application/json"
            )
        error_data = {
            "ok": False,
            "error": f"Camunda REST API error: {e.response.status_code}",
            "details": e.response.text,
            "endpoint": endpoint
        }
        return Response(
            content=json.dumps(error_data, indent=2, ensure_ascii=False),
            status_code=e.response.status_code,
            media_type="application/json"
        )
    except httpx.ConnectError:
        error_data = {
            "ok": False,
            "error": "Cannot connect to Camunda REST API",
            "camunda_url": CAMUNDA_REST_URL,
            "suggestion": "Make sure Camunda 8 is running on " + CAMUNDA_REST_URL
        }
        return Response(
            content=json.dumps(error_data, indent=2, ensure_ascii=False),
            status_code=503,
            media_type="application/json"
        )
    except Exception as e:
        error_data = {
            "ok": False,
            "error": "Failed to get user task details",
            "details": str(e),
            "suggestion": TASKLIST_API_SUGGESTION
        }
        return Response(
            content=json.dumps(error_data, indent=2, ensure_ascii=False),
            status_code=500,
            media_type="application/json"
        )


@app.post("/rpc/variables/search")
async def search_variables(request: dict):
    """Search process variables using Camunda REST API v2."""
    try:
        endpoint = "/v2/variables/search"
        result = await camunda_api_call("POST", endpoint, data=request)
        
        return {
            "ok": True,
            "variables": result.get("items", []),
            "totalCount": result.get("totalCount", 0),
            "page": result.get("page", {}),
            "request": request
        }
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            content={
                "ok": False,
                "error": f"Camunda REST API error: {e.response.status_code}",
                "details": e.response.text,
                "endpoint": endpoint
            },
            status_code=e.response.status_code
        )
    except httpx.ConnectError:
        return JSONResponse(
            content={
                "ok": False,
                "error": "Cannot connect to Camunda REST API",
                "camunda_url": CAMUNDA_REST_URL,
                "suggestion": "Make sure Camunda 8 is running on " + CAMUNDA_REST_URL
            },
            status_code=503
        )
    except Exception as e:
        return JSONResponse(
            content={
                "ok": False,
                "error": "Failed to search variables",
                "details": str(e),
                "suggestion": "Check your request format and try again"
            },
            status_code=500
        )


@app.get("/rpc/variables/{process_instance_key}")
async def get_variables_by_process(process_instance_key: str):
    """Get all variables for a specific process instance."""
    try:
        variables = await get_process_variables(process_instance_key)
        
        # Process variables for summary
        variable_summary = {
            "count": len(variables),
            "processInstanceKey": process_instance_key,
            "types": {},
            "names": []
        }
        
        processed_variables = {}
        for var_item in variables:
            var_name = var_item.get("name", "")
            var_type = var_item.get("type", "unknown")
            
            variable_summary["names"].append(var_name)
            
            # Count types
            if var_type in variable_summary["types"]:
                variable_summary["types"][var_type] += 1
            else:
                variable_summary["types"][var_type] = 1
            
            processed_variables[var_name] = {
                "value": var_item.get("value"),
                "type": var_type,
                "scope": var_item.get("scopeKey"),
                "processInstanceKey": var_item.get("processInstanceKey"),
                "raw": var_item
            }
        
        return {
            "ok": True,
            "processInstanceKey": process_instance_key,
            "summary": variable_summary,
            "variables": processed_variables,
            "rawData": variables
        }
    except Exception as e:
        return JSONResponse(
            content={
                "ok": False,
                "error": "Failed to get variables",
                "details": str(e),
                "processInstanceKey": process_instance_key
            },
            status_code=500
        )

# ====== Server startup ======
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Camunda 8 Proxy Server...")
    print("📊 Dashboard will be available at: http://localhost:8001")
    print(f"🔧 Zeebe Gateway: {ZEEBE_ADDRESS}")
    print(f"🌐 Camunda REST API: {CAMUNDA_REST_URL}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
