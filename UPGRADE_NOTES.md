# Upgrade to PyZeebe 4.7.0 - Notes

## Perubahan yang Dilakukan

### 1. Import gRPC Proto
- **Sebelum**: `from zeebe_grpc.gateway_pb2 import ...`
- **Sesudah**: Import dihapus karena User Task API tidak tersedia di pyzeebe 4.7.0

### 2. Deploy Process Method
- **Sebelum**: `zeebe_client.deploy_process()`
- **Sesudah**: `zeebe_client.deploy_resource()` (method telah diubah namanya)

### 3. User Task Operations
User Task operations telah diimplementasikan menggunakan gRPC manual:
### ✅ **User Task Endpoints (Manual gRPC Implementation):**
- `POST /rpc/user-task/complete` ✅ - Complete user task
- `POST /rpc/user-task/assign` ✅ - Assign user task
- `POST /rpc/user-task/unassign` ✅ - Unassign user task  
- `GET /rpc/user-task/{key}` ✅ - Get user task details

Implementasi menggunakan proto files custom dan gRPC stubs yang dikompilasi secara manual.

## Operasi yang Masih Berfungsi

✅ **Operasi Core yang berfungsi:**
- `GET /rpc/health` - Health check dan topology
- `POST /rpc/start` - Start process instance
- `POST /rpc/message` - Publish message
- `POST /rpc/cancel` - Cancel process instance  
- `POST /rpc/deploy` - Deploy BPMN (menggunakan deploy_resource)
- `GET /rpc/tasks` - List tasks via Elasticsearch

## Solusi untuk User Task Operations

Jika Anda memerlukan operasi User Task, Anda memiliki beberapa pilihan:

### Opsi 1: Gunakan Camunda 8 REST API
```python
import httpx

# Contoh complete user task via REST API
async def complete_user_task_rest(user_task_key: int, variables: dict):
    url = f"{camunda_base_url}/v1/user-tasks/{user_task_key}/completion"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"variables": variables}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
```

### Opsi 2: Implement gRPC langsung
Anda perlu:
1. Download proto files terbaru dari Camunda
2. Generate Python classes menggunakan `protoc`
3. Implement gRPC calls secara manual

### Opsi 3: Downgrade ke pyzeebe versi sebelumnya
Jika User Task operations sangat penting, pertimbangkan untuk menggunakan pyzeebe versi yang lebih lama yang mendukung User Task API.

## Testing

Untuk menjalankan aplikasi:

```bash
source venv/bin/activate
python app.py
```

Atau dengan uvicorn:

```bash
source venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Pastikan Anda telah mengatur environment variables yang diperlukan:

```bash
# Untuk koneksi lokal
ZEEBE_ADDRESS=localhost:26500

# Untuk Camunda Cloud/SaaS
ZEEBE_CLIENT_ID=your_client_id
ZEEBE_CLIENT_SECRET=your_client_secret
ZEEBE_AUTHORIZATION_SERVER_URL=https://login.cloud.camunda.io/oauth/token
ZEEBE_AUDIENCE=zeebe.camunda.io
ZEEBE_CLUSTER_ID=your_cluster_id

# Elasticsearch
ES_URL=http://localhost:9200
ES_USER=your_es_user
ES_PASS=your_es_password

# CORS
CORS_ORIGINS=*
```