# Web Screenshot Tool API 文档

## 概述

Web Screenshot Tool 现在支持多用户并发处理，每个用户都有独立的用户ID和任务ID，系统能够正确区分和返回每个用户的结果。

## API 端点

### 1. 提交任务

**端点**: `POST /api/submit`

**请求体**:
```json
{
    "user_id": "user_001",
    "urls": [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ]
}
```

**参数说明**:
- `user_id` (可选): 用户ID，如果不提供则使用 "anonymous"
- `urls` (必需): 要截图的URL列表

**响应示例**:
```json
{
    "success": true,
    "task_id": "user_001_12345678-1234-1234-1234-123456789abc",
    "user_id": "user_001",
    "urls_count": 3,
    "message": "任务已提交，任务ID: user_001_12345678-1234-1234-1234-123456789abc"
}
```

### 2. 查询任务状态

**端点**: `GET /api/status/{task_id}`

**响应示例**:
```json
{
    "task_id": "user_001_12345678-1234-1234-1234-123456789abc",
    "status": "processing",
    "progress": 66.7,
    "processed": 2,
    "total_urls": 3,
    "results": [],
    "error": null
}
```

**状态说明**:
- `processing`: 正在处理中
- `completed`: 处理完成
- `failed`: 处理失败

### 3. 下载PDF文件

**端点**: `GET /download/{task_id}/{result_index}`

**说明**: 下载特定任务的特定PDF文件

## 多用户并发特性

### 1. 用户隔离
- 每个用户都有独立的用户ID
- 任务ID包含用户ID前缀，便于识别
- 不同用户的任务完全隔离

### 2. 并发处理
- 支持多个用户同时提交任务
- 每个用户的任务独立处理
- 系统自动分配资源

### 3. 状态跟踪
- 每个任务都有独立的状态
- 实时进度更新
- 错误隔离，单个任务失败不影响其他任务

## 使用示例

### Python 示例

```python
import requests
import time

# API端点
BASE_URL = "http://localhost:5001"
SUBMIT_ENDPOINT = f"{BASE_URL}/api/submit"
STATUS_ENDPOINT = f"{BASE_URL}/api/status"

def submit_task(user_id, urls):
    """提交任务"""
    data = {
        "user_id": user_id,
        "urls": urls
    }
    
    response = requests.post(SUBMIT_ENDPOINT, json=data)
    return response.json()

def get_status(task_id):
    """获取任务状态"""
    response = requests.get(f"{STATUS_ENDPOINT}/{task_id}")
    return response.json()

# 使用示例
user_id = "user_001"
urls = ["https://example.com", "https://httpbin.org/html"]

# 提交任务
result = submit_task(user_id, urls)
if result['success']:
    task_id = result['task_id']
    print(f"任务提交成功: {task_id}")
    
    # 轮询状态
    while True:
        status = get_status(task_id)
        print(f"进度: {status['progress']}%")
        
        if status['status'] == 'completed':
            print("任务完成！")
            break
        elif status['status'] == 'failed':
            print(f"任务失败: {status['error']}")
            break
        
        time.sleep(2)
```

### cURL 示例

```bash
# 提交任务
curl -X POST http://localhost:5001/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "urls": ["https://example.com", "https://httpbin.org/html"]
  }'

# 查询状态
curl http://localhost:5001/api/status/user_001_12345678-1234-1234-1234-123456789abc

# 下载PDF
curl -O http://localhost:5001/download/user_001_12345678-1234-1234-1234-123456789abc/0
```

## 测试多用户并发

运行测试脚本：

```bash
python test_multi_users.py
```

这个脚本会模拟4个用户同时使用系统，测试并发处理能力。

## 性能特性

1. **并发处理**: 支持多个用户同时提交任务
2. **资源隔离**: 每个用户任务使用独立的浏览器实例
3. **错误隔离**: 单个任务失败不影响其他任务
4. **状态跟踪**: 实时显示每个任务的进度
5. **自动清理**: 任务完成后自动清理临时文件

## 注意事项

1. **用户ID**: 建议使用有意义的用户ID，便于管理和调试
2. **任务ID**: 任务ID包含用户ID前缀，便于识别任务归属
3. **并发限制**: 系统最多同时处理3个URL，可根据需要调整
4. **超时设置**: 建议设置合理的超时时间，避免长时间等待
5. **错误处理**: 注意处理网络异常和服务器错误 