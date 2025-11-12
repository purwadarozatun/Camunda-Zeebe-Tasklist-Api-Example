# Camunda 8 Proxy Server

FastAPI-based proxy server untuk Zeebe dan Camunda 8 REST API operations dengan web dashboard untuk testing dan monitoring.

## 🚀 Overview

Server ini menyediakan HTTP REST API wrapper untuk:
- **Zeebe gRPC Operations**: Process deployment, instance management, messaging
- **Camunda REST API v2**: User Task operations (complete, assign, unassign, list)
- **Web Dashboard**: Interactive interface untuk testing semua operations

## 📋 Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- Zeebe Gateway running (default: `localhost:26500`)
- Camunda 8 REST API (optional, untuk User Task operations)

## ⚙️ Installation & Setup

```bash
# Clone atau download project
cd camunda8-proxy

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python app.py
```

Server akan berjalan di: `http://localhost:8001`  
Dashboard tersedia di: `http://localhost:8001/`

## 🔧 Environment Variables

```bash
# Zeebe Configuration
ZEEBE_ADDRESS=localhost:26500
ZEEBE_CLIENT_ID=your_client_id
ZEEBE_CLIENT_SECRET=your_client_secret
ZEEBE_AUTHORIZATION_SERVER_URL=your_oauth_server
ZEEBE_AUDIENCE=your_audience
ZEEBE_CLUSTER_ID=your_cluster_id

# Camunda REST API Configuration
CAMUNDA_REST_URL=http://localhost:8080
CAMUNDA_REST_CLIENT_ID=your_client_id
CAMUNDA_REST_CLIENT_SECRET=your_client_secret

# Testing Mode (untuk development tanpa Camunda REST API)
MOCK_MODE=false

# CORS Configuration
CORS_ORIGINS=*
```

## 📚 API Documentation

### 🔍 Health Check

**Endpoint:** `GET /rpc/health`

**Kegunaan:** Memeriksa status koneksi ke Zeebe Gateway dan mendapatkan topology information.

**Response:**
```json
{
  "ok": true,
  "topology": {
    "brokers": [...],
    "cluster_size": 1,
    "partitions_count": 1,
    "replication_factor": 1,
    "gateway_version": "8.8.0"
  }
}
```

**Snippet Code:**
```javascript
// JavaScript
const response = await fetch('http://localhost:8001/rpc/health');
const health = await response.json();
console.log('Zeebe Status:', health.ok);
```

```python
# Python
import requests
response = requests.get('http://localhost:8001/rpc/health')
health = response.json()
print(f"Zeebe Status: {health['ok']}")
```

```bash
# cURL
curl -X GET "http://localhost:8001/rpc/health"
```

---

### 🏃‍♂️ Start Process Instance

**Endpoint:** `POST /rpc/start`

**Kegunaan:** Memulai instance baru dari BPMN process yang sudah di-deploy.

**Request Body:**
```json
{
  "bpmnProcessId": "order-process",
  "version": 1,
  "variables": {
    "orderId": "ORD-001",
    "customerEmail": "user@example.com",
    "amount": 50000
  }
}
```

**Parameters:**
- `bpmnProcessId` (string, required): ID dari BPMN process
- `version` (integer, optional): Versi process yang akan dijalankan. Jika kosong, akan menggunakan versi terbaru
- `variables` (object, optional): Initial variables untuk process instance

**Response:**
```json
{
  "ok": true,
  "processInstanceKey": 2251799813685249,
  "bpmnProcessId": "order-process",
  "version": 1,
  "processDefinitionKey": 2251799813685248
}
```

**Snippet Code:**
```javascript
// JavaScript
const startProcess = async () => {
  const body = {
    bpmnProcessId: "order-process",
    variables: {
      orderId: "ORD-001",
      customerEmail: "user@example.com",
      amount: 50000
    }
  };
  
  const response = await fetch('http://localhost:8001/rpc/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Process Instance Key:', result.processInstanceKey);
};
```

```python
# Python
import requests

def start_process():
    body = {
        "bpmnProcessId": "order-process",
        "variables": {
            "orderId": "ORD-001",
            "customerEmail": "user@example.com", 
            "amount": 50000
        }
    }
    
    response = requests.post(
        'http://localhost:8001/rpc/start',
        json=body
    )
    
    result = response.json()
    print(f"Process Instance Key: {result['processInstanceKey']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/start" \
  -H "Content-Type: application/json" \
  -d '{
    "bpmnProcessId": "order-process",
    "variables": {
      "orderId": "ORD-001",
      "customerEmail": "user@example.com",
      "amount": 50000
    }
  }'
```

---

### 📨 Publish Message

**Endpoint:** `POST /rpc/message`

**Kegunaan:** Mengirim message ke process instance yang sedang waiting di message catch event.

**Request Body:**
```json
{
  "messageName": "order_confirmed",
  "correlationKey": "ORD-001",
  "variables": {
    "confirmationDate": "2025-11-11",
    "confirmedBy": "customer"
  }
}
```

**Parameters:**
- `messageName` (string, required): Nama message yang didefinisikan di BPMN
- `correlationKey` (string, required): Key untuk menentukan process instance mana yang akan menerima message
- `variables` (object, optional): Additional variables yang akan di-merge ke process instance

**Response:**
```json
{
  "ok": true,
  "key": 2251799813685250
}
```

**Snippet Code:**
```javascript
// JavaScript
const publishMessage = async () => {
  const body = {
    messageName: "order_confirmed",
    correlationKey: "ORD-001",
    variables: {
      confirmationDate: "2025-11-11",
      confirmedBy: "customer"
    }
  };
  
  const response = await fetch('http://localhost:8001/rpc/message', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Message Key:', result.key);
};
```

```python
# Python
import requests

def publish_message():
    body = {
        "messageName": "order_confirmed",
        "correlationKey": "ORD-001",
        "variables": {
            "confirmationDate": "2025-11-11",
            "confirmedBy": "customer"
        }
    }
    
    response = requests.post(
        'http://localhost:8001/rpc/message',
        json=body
    )
    
    result = response.json()
    print(f"Message Key: {result['key']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/message" \
  -H "Content-Type: application/json" \
  -d '{
    "messageName": "order_confirmed",
    "correlationKey": "ORD-001",
    "variables": {
      "confirmationDate": "2025-11-11",
      "confirmedBy": "customer"
    }
  }'
```

---

### ⏹️ Cancel Process Instance

**Endpoint:** `POST /rpc/cancel`

**Kegunaan:** Membatalkan process instance yang sedang berjalan.

**Request Body:**
```json
{
  "processInstanceKey": 2251799813685249
}
```

**Parameters:**
- `processInstanceKey` (integer, required): Key dari process instance yang akan dibatalkan

**Response:**
```json
{
  "ok": true
}
```

**Snippet Code:**
```javascript
// JavaScript
const cancelInstance = async (processInstanceKey) => {
  const body = { processInstanceKey: Number(processInstanceKey) };
  
  const response = await fetch('http://localhost:8001/rpc/cancel', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Cancelled:', result.ok);
};
```

```python
# Python
import requests

def cancel_instance(process_instance_key):
    body = {"processInstanceKey": int(process_instance_key)}
    
    response = requests.post(
        'http://localhost:8001/rpc/cancel',
        json=body
    )
    
    result = response.json()
    print(f"Cancelled: {result['ok']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/cancel" \
  -H "Content-Type: application/json" \
  -d '{"processInstanceKey": 2251799813685249}'
```

---

### 📦 Deploy BPMN Process

**Endpoint:** `POST /rpc/deploy`

**Kegunaan:** Deploy BPMN file yang ada di server ke Zeebe.

**Request Body:**
```json
{
  "bpmnPath": "./bpmn/order-process.bpmn"
}
```

**Parameters:**
- `bpmnPath` (string, required): Path ke file BPMN di server (bukan upload dari client)

**Response:**
```json
{
  "ok": true,
  "key": 2251799813685248,
  "processes": [
    {
      "bpmnProcessId": "order-process",
      "version": 1,
      "processDefinitionKey": 2251799813685248,
      "resourceName": "order-process.bpmn"
    }
  ]
}
```

**Snippet Code:**
```javascript
// JavaScript
const deployBPMN = async (bpmnPath) => {
  const body = { bpmnPath: bpmnPath };
  
  const response = await fetch('http://localhost:8001/rpc/deploy', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Deployed Processes:', result.processes);
};
```

```python
# Python
import requests

def deploy_bpmn(bpmn_path):
    body = {"bpmnPath": bpmn_path}
    
    response = requests.post(
        'http://localhost:8001/rpc/deploy',
        json=body
    )
    
    result = response.json()
    print(f"Deployed Processes: {result['processes']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/deploy" \
  -H "Content-Type: application/json" \
  -d '{"bpmnPath": "./bpmn/order-process.bpmn"}'
```

---

## 👤 User Task Operations

> **⚠️ Note:** User Task operations membutuhkan Camunda 8 REST API yang berjalan di port 8080. Jika tidak tersedia, gunakan `MOCK_MODE=true` untuk testing.

### 📋 List User Tasks

**Endpoint:** `GET /rpc/tasks`

**Kegunaan:** Mendapatkan daftar user tasks berdasarkan assignee.

**Query Parameters:**
- `assignee` (string, required): Username assignee untuk filter tasks

**Response:**
```json
{
  "ok": true,
  "count": 2,
  "tasks": [
    {
      "userTaskKey": "2251799813685251",
      "taskName": "approve-order",
      "assignee": "demo",
      "processInstanceKey": "2251799813685249",
      "intent": "CREATED",
      "timestamp": "2025-11-11T10:30:00Z",
      "formKey": null,
      "variables": {}
    }
  ]
}
```

**Snippet Code:**
```javascript
// JavaScript
const fetchTasks = async (assignee) => {
  const response = await fetch(`http://localhost:8001/rpc/tasks?assignee=${encodeURIComponent(assignee)}`);
  const data = await response.json();
  console.log('Tasks:', data.tasks);
  return data.tasks;
};
```

```python
# Python
import requests

def fetch_tasks(assignee):
    response = requests.get(f'http://localhost:8001/rpc/tasks?assignee={assignee}')
    data = response.json()
    print(f"Tasks: {data['tasks']}")
    return data['tasks']
```

```bash
# cURL
curl -X GET "http://localhost:8001/rpc/tasks?assignee=demo"
```

---

### 🤝 Assign User Task

**Endpoint:** `POST /rpc/user-task/assign`

**Kegunaan:** Assign user task ke specific user.

**Request Body:**
```json
{
  "userTaskKey": 2251799813685251,
  "assignee": "demo",
  "allowOverride": true
}
```

**Parameters:**
- `userTaskKey` (integer, required): Key dari user task
- `assignee` (string, required): Username yang akan di-assign
- `allowOverride` (boolean, optional): Allow override existing assignment (default: false)

**Response:**
```json
{
  "ok": true,
  "result": {}
}
```

**Snippet Code:**
```javascript
// JavaScript
const assignTask = async (userTaskKey, assignee) => {
  const body = {
    userTaskKey: Number(userTaskKey),
    assignee: assignee,
    allowOverride: true
  };
  
  const response = await fetch('http://localhost:8001/rpc/user-task/assign', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Assigned:', result.ok);
};
```

```python
# Python
import requests

def assign_task(user_task_key, assignee):
    body = {
        "userTaskKey": int(user_task_key),
        "assignee": assignee,
        "allowOverride": True
    }
    
    response = requests.post(
        'http://localhost:8001/rpc/user-task/assign',
        json=body
    )
    
    result = response.json()
    print(f"Assigned: {result['ok']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/user-task/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "userTaskKey": 2251799813685251,
    "assignee": "demo",
    "allowOverride": true
  }'
```

---

### 🔄 Unassign User Task

**Endpoint:** `POST /rpc/user-task/unassign`

**Kegunaan:** Remove assignment dari user task.

**Request Body:**
```json
{
  "userTaskKey": 2251799813685251
}
```

**Parameters:**
- `userTaskKey` (integer, required): Key dari user task yang akan di-unassign

**Response:**
```json
{
  "ok": true,
  "result": {}
}
```

**Snippet Code:**
```javascript
// JavaScript
const unassignTask = async (userTaskKey) => {
  const body = { userTaskKey: Number(userTaskKey) };
  
  const response = await fetch('http://localhost:8001/rpc/user-task/unassign', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Unassigned:', result.ok);
};
```

```python
# Python
import requests

def unassign_task(user_task_key):
    body = {"userTaskKey": int(user_task_key)}
    
    response = requests.post(
        'http://localhost:8001/rpc/user-task/unassign',
        json=body
    )
    
    result = response.json()
    print(f"Unassigned: {result['ok']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/user-task/unassign" \
  -H "Content-Type: application/json" \
  -d '{"userTaskKey": 2251799813685251}'
```

---

### ✅ Complete User Task

**Endpoint:** `POST /rpc/user-task/complete`

**Kegunaan:** Complete user task dan melanjutkan process flow.

**Request Body:**
```json
{
  "userTaskKey": 2251799813685251,
  "variables": {
    "approved": true,
    "approverComment": "Order looks good",
    "approvalDate": "2025-11-11"
  }
}
```

**Parameters:**
- `userTaskKey` (integer, required): Key dari user task yang akan di-complete
- `variables` (object, optional): Variables yang akan di-set saat complete task

**Response:**
```json
{
  "ok": true,
  "result": {}
}
```

**Snippet Code:**
```javascript
// JavaScript
const completeTask = async (userTaskKey, variables = {}) => {
  const body = {
    userTaskKey: Number(userTaskKey),
    variables: variables
  };
  
  const response = await fetch('http://localhost:8001/rpc/user-task/complete', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  
  const result = await response.json();
  console.log('Completed:', result.ok);
};
```

```python
# Python
import requests

def complete_task(user_task_key, variables=None):
    body = {
        "userTaskKey": int(user_task_key),
        "variables": variables or {}
    }
    
    response = requests.post(
        'http://localhost:8001/rpc/user-task/complete',
        json=body
    )
    
    result = response.json()
    print(f"Completed: {result['ok']}")
```

```bash
# cURL
curl -X POST "http://localhost:8001/rpc/user-task/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "userTaskKey": 2251799813685251,
    "variables": {
      "approved": true,
      "approverComment": "Order looks good",
      "approvalDate": "2025-11-11"
    }
  }'
```

---

### 🔍 Get User Task Details

**Endpoint:** `GET /rpc/user-task/{key}`

**Kegunaan:** Mendapatkan detail lengkap dari specific user task.

**Path Parameters:**
- `key` (integer, required): User Task Key

**Response:**
```json
{
  "ok": true,
  "task": {
    "userTaskKey": "2251799813685251",
    "taskName": "approve-order",
    "assignee": "demo",
    "processInstanceKey": "2251799813685249",
    "state": "CREATED",
    "formKey": null,
    "variables": {},
    "creationTime": "2025-11-11T10:30:00Z"
  }
}
```

**Snippet Code:**
```javascript
// JavaScript
const getTaskDetails = async (userTaskKey) => {
  const response = await fetch(`http://localhost:8001/rpc/user-task/${userTaskKey}`);
  const data = await response.json();
  console.log('Task Details:', data.task);
  return data.task;
};
```

```python
# Python
import requests

def get_task_details(user_task_key):
    response = requests.get(f'http://localhost:8001/rpc/user-task/{user_task_key}')
    data = response.json()
    print(f"Task Details: {data['task']}")
    return data['task']
```

```bash
# cURL
curl -X GET "http://localhost:8001/rpc/user-task/2251799813685251"
```

---

## 🌐 Web Dashboard

Dashboard web interaktif tersedia di `http://localhost:8001/` yang menyediakan:

### Features:
- **Configuration Panel**: Set base URL, process ID, variables
- **Process Operations**: Start, message, cancel, deploy
- **User Task Management**: List, assign, unassign, complete
- **Real-time Logging**: See API calls dan responses
- **Task Table**: Interactive table untuk select tasks

### Usage:
1. Buka `http://localhost:8001/` di browser
2. Konfigurasi base URL (default: `http://localhost:8001`)
3. Set process ID dan variables sesuai kebutuhan
4. Gunakan buttons untuk testing operations
5. Monitor results di log panel

---

## 🔧 Development & Testing

### Mock Mode
Untuk testing tanpa Camunda REST API:

```bash
export MOCK_MODE=true
python app.py
```

### Testing dengan cURL
```bash
# Test health check
curl http://localhost:8001/rpc/health

# Start process
curl -X POST http://localhost:8001/rpc/start \
  -H "Content-Type: application/json" \
  -d '{"bpmnProcessId": "test-process", "variables": {}}'
```

### Python Client Example
```python
import requests
import json

class CamundaProxyClient:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
    
    def health_check(self):
        return requests.get(f"{self.base_url}/rpc/health").json()
    
    def start_process(self, process_id, variables=None):
        body = {
            "bpmnProcessId": process_id,
            "variables": variables or {}
        }
        return requests.post(
            f"{self.base_url}/rpc/start", 
            json=body
        ).json()
    
    def list_tasks(self, assignee):
        return requests.get(
            f"{self.base_url}/rpc/tasks?assignee={assignee}"
        ).json()
    
    def complete_task(self, task_key, variables=None):
        body = {
            "userTaskKey": int(task_key),
            "variables": variables or {}
        }
        return requests.post(
            f"{self.base_url}/rpc/user-task/complete",
            json=body
        ).json()

# Usage
client = CamundaProxyClient()
print(client.health_check())
```

---

## 🚨 Error Handling

### Common Errors:

**1. Zeebe Connection Error**
```json
{
  "detail": "Failed to connect to Zeebe Gateway at localhost:26500"
}
```
**Solution:** Pastikan Zeebe Gateway running di port 26500

**2. Camunda REST API Unavailable**  
```json
{
  "detail": {
    "error": "Cannot connect to Camunda REST API",
    "camunda_url": "http://localhost:8080",
    "suggestion": "Make sure Camunda 8 is running on http://localhost:8080"
  }
}
```
**Solution:** Start Camunda 8 REST API atau enable `MOCK_MODE=true`

**3. Process Not Found**
```json
{
  "detail": "Process with BPMN process id 'unknown-process' not found"
}
```
**Solution:** Deploy BPMN process terlebih dahulu atau gunakan process ID yang benar

**4. Task Not Found**
```json
{
  "detail": {
    "error": "User task not found",
    "taskKey": 123
  }
}
```
**Solution:** Pastikan task key benar dan task masih exists

---

## 📝 Changelog

### Version 2.0 (Current)
- ✅ Upgraded to pyzeebe 4.7.0 
- ✅ Implemented Camunda REST API v2 untuk User Task operations
- ✅ Added comprehensive error handling
- ✅ Created interactive web dashboard  
- ✅ Removed Elasticsearch dependencies
- ✅ Added mock mode untuk development
- ✅ Enhanced logging dan debugging

### Version 1.0 (Previous)
- Basic Zeebe operations via pyzeebe
- Elasticsearch integration untuk task listing
- Simple HTTP endpoints

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

[Add your license information here]

---

## 🔍 Advanced Features

### Get Process Variables

**Endpoint:** `GET /rpc/variables/{process_instance_key}`

Get all variables for a specific process instance:

**JavaScript Example:**
```javascript
const processInstanceKey = "2251799813699499";
const response = await fetch(`http://localhost:8001/rpc/variables/${processInstanceKey}`);
const data = await response.json();
console.log('Variables:', data.variables);
```

**Python Example:**
```python
import requests

process_instance_key = "2251799813699499"
response = requests.get(f"http://localhost:8001/rpc/variables/{process_instance_key}")
data = response.json()
print(f"Found {data['summary']['count']} variables")
```

### Search Variables with Filters

**Endpoint:** `POST /rpc/variables/search`

Advanced variable search using Camunda REST API v2:

**JavaScript Example:**
```javascript
const searchRequest = {
  "filter": {
    "processInstanceKey": {"$eq": "2251799813699499"},
    "scopeKey": {"$eq": "2251799813699499"}
  },
  "page": {"from": 0, "limit": 50},
  "sort": [{"field": "name", "order": "asc"}]
};

const response = await fetch('http://localhost:8001/rpc/variables/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(searchRequest)
});
const data = await response.json();
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8001/rpc/variables/search" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "processInstanceKey": {"$eq": "2251799813699499"},
      "scopeKey": {"$eq": "2251799813699499"}
    },
    "page": {"from": 0, "limit": 50},
    "sort": [{"field": "name", "order": "asc"}]
  }'
```

## 🤖 Job Worker - WhatsApp Notification

Project ini menyertakan job worker untuk menangani pengiriman notifikasi WhatsApp dalam workflow Camunda.

### File Worker

**Files:**
- `worker_notifikasi_wa_simple.py` - Skeleton dasar (memerlukan perbaikan untuk pyzeebe 4.7.0)
- `worker_simple_working.py` - Mock version untuk testing
- `worker_wa_fixed.py` - **✅ pyzeebe 4.7.0 Compatible Version** (Recommended)

Worker ini menangani job dengan nama `kirim-notifikasi-wa` dan bertugas untuk mengirim notifikasi WhatsApp kepada customer dalam workflow business process.

### Setup & Usage

#### 1. Setup Environment
```bash
# Aktivasi virtual environment
source venv/bin/activate

# Install pyzeebe 4.7.0
pip install pyzeebe==4.7.0

# Pastikan Zeebe running di localhost:26500
```

#### 2. Test Worker Locally
```bash
# Test function tanpa koneksi Zeebe
python worker_wa_fixed.py --test
```

#### 3. Run Real Worker
```bash
# Connect ke Zeebe dan tunggu jobs
python worker_wa_fixed.py
```

### Job Variables

**Required Variables:**
- `phone_number` (string) - Nomor HP target (required)
- `message` (string) - Template pesan dengan placeholder (required)

**Optional Variables:**
- `customer_name` (string) - Nama customer, default: "Customer"
- `order_id` (string) - ID pesanan

**Message Template Support:**
```json
{
  "phone_number": "08123456789",
  "message": "Halo {customer_name}, pesanan {order_id} telah dikonfirmasi pada {timestamp}",
  "customer_name": "John Doe",
  "order_id": "ORD-12345"
}
```

**Response Variables:**
- Success: `status`, `sent_at`, `phone_number`, `message_delivered`, `delivery_id`, `message_content`
- Failed: `status`, `error`, `failed_at`, `phone_number`, `retry_recommended`

### Implementation (pyzeebe 4.7.0)

```python
#!/usr/bin/env python3
"""WhatsApp Worker - pyzeebe 4.7.0 Compatible"""

import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel

# Create connection
channel = create_insecure_channel("localhost:26500")
worker = ZeebeWorker(channel)

# Register job handler
@worker.task(task_type="kirim-notifikasi-wa")
def handle_whatsapp_job(
    phone_number: str,
    message: str,
    customer_name: str = "Customer", 
    order_id: str = ""
) -> dict:
    # Process WhatsApp notification
    return {"status": "success", "delivery_id": "wa_123"}

# Run worker
async def main():
    await worker.work()

if __name__ == '__main__':
    asyncio.run(main())

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-worker")

def kirim_notifikasi_wa(job):
    """Handler untuk job 'kirim-notifikasi-wa'"""
    
    logger.info(f"Processing job: {job.key}")
    
    # Extract variables
    variables = job.variables
    phone_number = variables.get("phone_number", "")
    message = variables.get("message", "")
    
    # Validasi
    if not phone_number or not message:
        return {"status": "failed", "error": "Missing variables"}
    
    # Simulasi pengiriman WhatsApp
    logger.info(f"Sending WhatsApp to: {phone_number}")
    
    # TODO: Implementasi API WhatsApp yang sebenarnya
    # success = send_whatsapp_api(phone_number, message)
    
    return {
        "status": "success",
        "sent_at": datetime.now().isoformat(),
        "phone_number": phone_number
    }

async def main():
    """Main worker function"""
    from pyzeebe import ZeebeClient, create_insecure_channel
    
    # Create client and worker
    channel = create_insecure_channel(grpc_address=ZEEBE_ADDRESS)
    client = ZeebeClient(channel)
    
    worker = client.create_worker(
        task_type=JOB_TYPE,
        task_handler=kirim_notifikasi_wa,
        max_jobs_to_activate=3,
        timeout_ms=30000
    )
    
    logger.info("Worker started! Waiting for jobs...")
    await worker

if __name__ == "__main__":
    asyncio.run(main())
```

### Testing Worker

Untuk test worker dengan mock job:

```python
# Test dengan simulasi job
class MockJob:
    def __init__(self, variables):
        self.variables = variables
        self.key = "test-job-123"

# Test variables
test_vars = {
    "phone_number": "08123456789",
    "message": "Test pesan WhatsApp",
    "customer_name": "Test Customer"
}

# Run test
result = kirim_notifikasi_wa(MockJob(test_vars))
print(f"Test result: {result}")
```

### Integration dengan BPMN

Dalam BPMN, tambahkan Service Task dengan:

**Task Definition:**
- **Type:** `kirim-notifikasi-wa`
- **Input Variables:** `phone_number`, `message`
- **Output Variables:** `wa_status`, `wa_sent_at`

**BPMN Example:**
```xml
<bpmn:serviceTask id="SendWhatsApp" name="Kirim Notifikasi WA">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="kirim-notifikasi-wa" />
    <zeebe:ioMapping>
      <zeebe:input source="customerPhone" target="phone_number" />
      <zeebe:input source="notificationMessage" target="message" />
      <zeebe:output source="status" target="wa_status" />
      <zeebe:output source="sent_at" target="wa_sent_at" />
    </zeebe:ioMapping>
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

### Production Setup

Untuk production, customize worker dengan:

1. **WhatsApp API Integration**
   ```python
   import requests
   
   def send_whatsapp_api(phone_number, message):
       # Implementasi dengan WhatsApp Business API
       headers = {"Authorization": f"Bearer {API_TOKEN}"}
       payload = {
           "messaging_product": "whatsapp",
           "to": phone_number,
           "type": "text",
           "text": {"body": message}
       }
       response = requests.post(API_URL, json=payload, headers=headers)
       return response.status_code == 200
   ```

2. **Error Handling & Retry**
   ```python
   def kirim_notifikasi_wa(job):
       try:
           # Attempt to send
           success = send_whatsapp_api(phone_number, message)
           if not success:
               # Return incident untuk retry
               raise Exception("WhatsApp API failed")
       except Exception as e:
           # Log error dan return failure
           return {"status": "failed", "error": str(e)}
   ```

3. **Environment Configuration**
   ```bash
   # .env file
   ZEEBE_ADDRESS=localhost:26500
   WHATSAPP_API_URL=https://graph.facebook.com/v17.0/YOUR_PHONE_ID/messages
   WHATSAPP_API_TOKEN=your_whatsapp_token
   ```

## 🆘 Support & Contact

Untuk pertanyaan atau issue:
1. Check error logs di terminal
2. Verify environment variables
3. Test dengan web dashboard
4. Check Zeebe/Camunda connectivity

**Happy workflow automation! 🎉**