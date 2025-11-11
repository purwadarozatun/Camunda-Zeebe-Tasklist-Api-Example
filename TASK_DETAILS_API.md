# 📋 Task Details API - Sample Usage

## 🎯 API Endpoint

### Get Task Details (Pretty JSON)
**Endpoint:** `GET /rpc/user-task/{key}/pretty`

**Kegunaan:** Mendapatkan detail lengkap task dalam format JSON yang rapi dan mudah dibaca.

**Path Parameters:**
- `key` (string, required): User Task Key

**Response Format:**
```json
{
  "ok": true,
  "taskKey": "2251799813685251",
  "taskDetails": {
    // Raw response from Camunda REST API
  },
  "formatted": {
    "userTaskKey": "2251799813685251",
    "taskName": "approve-order",
    "assignee": "demo",
    "processInstanceKey": "2251799813685249",
    "state": "CREATED",
    "creationDate": "2025-11-11T10:30:00.000Z",
    "completionDate": null,
    "formKey": null,
    "processDefinitionKey": "2251799813685248",
    "variables": {
      "orderId": "ORD-001",
      "amount": 50000
    }
  }
}
```

## 🌐 Web Interface Usage

1. **Buka Dashboard:** `http://localhost:8001`
2. **List Tasks:** Click "📋 List Tasks" untuk mendapatkan daftar tasks
3. **Select Task:** Click pada row di tabel untuk memilih task (User Task Key akan otomatis terisi)
4. **Get Details:** Click "🔍 Get Details (Pretty JSON)" untuk mendapatkan detail dalam format JSON
5. **View Result:** Lihat hasil di area "Task Details (Pretty JSON)" di bawah tabel

## 💻 Code Examples

### JavaScript (Browser)
```javascript
const getTaskDetails = async (taskKey) => {
  try {
    const response = await fetch(`http://localhost:8001/rpc/user-task/${taskKey}/pretty`);
    const data = await response.json();
    
    if (data.ok) {
      console.log('Task Details:', JSON.stringify(data, null, 2));
      return data;
    } else {
      console.error('Error:', data.error);
      return null;
    }
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
};

// Usage
getTaskDetails('2251799813685251');
```

### Python
```python
import requests
import json

def get_task_details(task_key, base_url="http://localhost:8001"):
    try:
        response = requests.get(f"{base_url}/rpc/user-task/{task_key}/pretty")
        data = response.json()
        
        if data.get('ok'):
            print("Task Details (Pretty JSON):")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"Error: {data.get('error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

# Usage
get_task_details('2251799813685251')
```

### cURL
```bash
# Get task details in pretty JSON format
curl -s "http://localhost:8001/rpc/user-task/2251799813685251/pretty" | jq

# Or without jq (already formatted)
curl -s "http://localhost:8001/rpc/user-task/2251799813685251/pretty"
```

## 🔧 Features

### ✅ **Included Features:**
- **Pretty JSON Format:** Response sudah di-format dengan indentasi 2 spasi
- **Raw Data:** Menyediakan response asli dari Camunda REST API
- **Formatted Data:** Data yang sudah di-format untuk kemudahan pembacaan
- **Error Handling:** Error messages yang jelas dan informatif
- **Web Interface:** UI yang mudah digunakan di dashboard

### 📊 **Response Structure:**
- `ok`: Status boolean operation
- `taskKey`: Key task yang diminta
- `taskDetails`: Raw response dari Camunda REST API
- `formatted`: Data yang sudah diformat dengan field-field penting

### 🚨 **Error Cases:**
- **404 Not Found:** Task tidak ditemukan
- **503 Service Unavailable:** Camunda REST API tidak tersedia
- **500 Internal Server Error:** Error server internal

## 🎮 Testing Workflow

1. **Start Process Instance:**
   ```bash
   curl -X POST http://localhost:8001/rpc/start \
     -H "Content-Type: application/json" \
     -d '{"bpmnProcessId": "order-process", "variables": {"orderId": "ORD-001"}}'
   ```

2. **List Available Tasks:**
   ```bash
   curl "http://localhost:8001/rpc/tasks?assignee=demo"
   ```

3. **Get Task Details (Pretty JSON):**
   ```bash
   curl "http://localhost:8001/rpc/user-task/TASK_KEY_HERE/pretty"
   ```

4. **Assign Task:**
   ```bash
   curl -X POST http://localhost:8001/rpc/user-task/assign \
     -H "Content-Type: application/json" \
     -d '{"userTaskKey": TASK_KEY, "assignee": "demo", "allowOverride": true}'
   ```

5. **Complete Task:**
   ```bash
   curl -X POST http://localhost:8001/rpc/user-task/complete \
     -H "Content-Type: application/json" \
     -d '{"userTaskKey": TASK_KEY, "variables": {"approved": true}}'
   ```

## 💡 Tips & Best Practices

1. **Always Check Task Key:** Pastikan User Task Key valid sebelum request
2. **Handle Errors:** Selalu handle kemungkinan error (404, 503, 500)
3. **Use Pretty Format:** Endpoint `/pretty` memberikan format JSON yang lebih mudah dibaca
4. **Log Responses:** Gunakan area log di dashboard untuk tracking API calls
5. **Mock Mode:** Set `MOCK_MODE=true` untuk testing tanpa Camunda REST API

## 🔗 Related Endpoints

- `GET /rpc/tasks` - List user tasks
- `GET /rpc/user-task/{key}` - Get task details (compact format)
- `POST /rpc/user-task/assign` - Assign task
- `POST /rpc/user-task/complete` - Complete task
- `POST /rpc/user-task/unassign` - Unassign task

Happy task management! 🎉