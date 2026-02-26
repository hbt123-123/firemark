# Plan Agent Backend API 接口文档

> 适用于 Flutter 前端开发  
> 版本：v1.0.0  
> 基础 URL: `http://localhost:8000/api/v1`

---

## 目录

1. [认证与授权](#1-认证与授权)
2. [Agent 智能体](#2-agent-智能体)
3. [任务管理](#3-任务管理)
4. [执行跟踪](#4-执行跟踪)
5. [反思与调整](#5-反思与调整)
6. [用户设置](#6-用户设置)
7. [错误处理](#7-错误处理)
8. [单词学习](#8-单词学习)

---

## 1. 认证与授权

### 1.1 用户注册

```
POST /api/v1/auth/register
```

**请求体:**
```json
{
  "username": "string (3-80 字符)",
  "password": "string (最少 6 字符)"
}
```

**响应:** `UserResponse`
```json
{
  "id": 1,
  "username": "john_doe",
  "created_at": "2026-02-23T12:00:00Z"
}
```

**Flutter 示例:**
```dart
Future<UserResponse> register(String username, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/register'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'username': username, 'password': password}),
  );
  
  if (response.statusCode == 201) {
    return UserResponse.fromJson(jsonDecode(response.body));
  } else {
    throw ApiException(jsonDecode(response.body)['detail']);
  }
}
```

---

### 1.2 用户登录 (JSON)

```
POST /api/v1/auth/login
```

**请求体:**
```json
{
  "username": "john_doe",
  "password": "password123"
}
```

**响应:** `Token`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 1.3 用户登录 (表单)

```
POST /api/v1/auth/login/form
```

**请求体 (application/x-www-form-urlencoded):**
```
username=john_doe&password=password123
```

**响应:** `Token` (同上)

---

### 1.4 获取当前用户信息

```
GET /api/v1/auth/me
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**响应:** `UserResponse`

---

## 2. Agent 智能体

### 2.1 智能对话

```
POST /api/v1/agent/chat
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "message": "我想学习 Python",
  "session_id": "session_abc123"  // 可选，用于保持会话连续性
}
```

**响应:** `ChatResponse`
```json
{
  "success": true,
  "response": "好的，我来帮你制定一个 Python 学习计划...",
  "session_id": "session_abc123",
  "intent": "create_plan",
  "entities": {"language": "Python", "goal": "learning"}
}
```

**Flutter 示例:**
```dart
Future<ChatResponse> chat(String message, {String? sessionId}) async {
  final response = await http.post(
    Uri.parse('$baseUrl/agent/chat'),
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    },
    body: jsonEncode({
      'message': message,
      'session_id': sessionId,
    }),
  );
  
  return ChatResponse.fromJson(jsonDecode(response.body));
}
```

---

### 2.2 直接执行 Skill

```
POST /api/v1/agent/skill
```

**请求体:**
```json
{
  "skill_name": "generate_plan",
  "parameters": {
    "goal_id": 123,
    "additional_context": "我希望每天学习 2 小时"
  }
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "outline": {...},
    "tasks": [...],
    "recommendations": [...]
  }
}
```

**可用 Skills:**
- `generate_plan` - 生成学习计划
- `adjust_tasks` - 调整任务计划

---

### 2.3 获取可用插件列表

```
GET /api/v1/agent/plugins
```

**响应:**
```json
{
  "skills": [
    {"name": "generate_plan", "description": "..."},
    {"name": "adjust_tasks", "description": "..."}
  ],
  "tools": [
    {"name": "web_search", "description": "..."},
    {"name": "db_query", "description": "..."},
    {"name": "send_notification", "description": "..."}
  ]
}
```

---

### 2.4 清除会话

```
DELETE /api/v1/agent/session/{session_id}
```

**响应:**
```json
{
  "success": true,
  "message": "Session session_abc123 cleared"
}
```

---

## 3. 任务管理

### 3.1 创建任务

```
POST /api/v1/tasks
```

**请求体:**
```json
{
  "title": "学习 Python 基础",
  "description": "完成 Python 入门教程",
  "goal_id": 1,  // 可选
  "fixed_schedule_id": null,  // 可选
  "due_date": "2026-02-25",
  "due_time": "14:00",  // 可选，格式 HH:MM
  "priority": 1,  // 0=低，1=中，2=高
  "dependencies": []  // 前置任务 ID 列表
}
```

**响应:** `TaskResponse`
```json
{
  "id": 456,
  "user_id": 1,
  "goal_id": 1,
  "title": "学习 Python 基础",
  "description": "完成 Python 入门教程",
  "due_date": "2026-02-25",
  "due_time": "14:00",
  "status": "pending",
  "priority": 1,
  "dependencies": [],
  "created_at": "2026-02-23T12:00:00Z"
}
```

---

### 3.2 获取任务列表

```
GET /api/v1/tasks
```

**查询参数:**
- `status` - 过滤状态 (pending/completed/skipped)
- `due_date` - 过滤日期 (YYYY-MM-DD)
- `goal_id` - 过滤目标 ID
- `priority` - 过滤优先级 (0/1/2)
- `skip` - 跳过的记录数 (默认 0)
- `limit` - 返回数量 (默认 20，最大 100)

**示例:**
```
GET /api/v1/tasks?status=pending&due_date=2026-02-25&limit=10
```

**响应:**
```json
{
  "tasks": [...],
  "total": 15
}
```

---

### 3.3 获取今日任务

```
GET /api/v1/tasks/today
```

**响应:** `TaskListResponse` (同上)

---

### 3.4 获取单个任务

```
GET /api/v1/tasks/{task_id}
```

**响应:** `TaskResponse`

---

### 3.5 更新任务

```
PUT /api/v1/tasks/{task_id}
```

**请求体 (所有字段可选):**
```json
{
  "title": "更新后的标题",
  "description": "更新后的描述",
  "priority": 2,
  "status": "completed",
  "due_date": "2026-02-26",
  "due_time": "15:00"
}
```

**响应:** `TaskResponse`

---

### 3.6 删除任务

```
DELETE /api/v1/tasks/{task_id}
```

**响应:**
```json
{
  "success": true,
  "message": "Task deleted"
}
```

---

### 3.7 完成任务

```
POST /api/v1/tasks/{task_id}/complete
```

**响应:** `TaskResponse` (status 变为 "completed")

---

### 3.8 跳过任务

```
POST /api/v1/tasks/{task_id}/skip
```

**响应:** `TaskResponse` (status 变为 "skipped")

---

### 3.9 批量更新状态

```
POST /api/v1/tasks/batch-update-status?status=completed
```

**请求体:**
```json
[1, 2, 3]  // 任务 ID 列表
```

**响应:**
```json
{
  "success": true,
  "updated_count": 3,
  "message": "Updated 3 tasks to completed"
}
```

---

## 4. 执行跟踪

### 4.1 获取执行日志列表

```
GET /api/v1/execution/logs
```

**查询参数:**
- `start_date` - 开始日期 (YYYY-MM-DD)
- `end_date` - 结束日期 (YYYY-MM-DD)

**响应:** `List<ExecutionLogResponse>`
```json
[
  {
    "id": 1,
    "user_id": 1,
    "log_date": "2026-02-23",
    "tasks_completed": 5,
    "tasks_total": 8,
    "difficulties": "时间不够用",
    "feedback": "需要更好地规划时间",
    "created_at": "2026-02-23T23:55:00Z"
  }
]
```

---

### 4.2 获取单日执行日志

```
GET /api/v1/execution/logs/{log_date}
```

**示例:** `GET /api/v1/execution/logs/2026-02-23`

**响应:** `ExecutionLogResponse`

---

### 4.3 获取执行统计

```
GET /api/v1/execution/stats
```

**查询参数:**
- `start_date` - 开始日期
- `end_date` - 结束日期

**响应:** `ExecutionStatsResponse`
```json
{
  "total_days": 30,
  "total_tasks": 150,
  "total_completed": 120,
  "average_completion_rate": 80.5,
  "streak_days": 7
}
```

---

### 4.4 更新执行反馈

```
POST /api/v1/execution/logs/{log_date}/feedback
```

**请求体:**
```json
{
  "difficulties": "今天工作太忙",
  "feedback": "明天需要早起学习"
}
```

**响应:** `ExecutionLogResponse`

---

### 4.5 生成每日日志

```
POST /api/v1/execution/logs/generate?log_date=2026-02-23
```

**响应:**
```json
{
  "success": true,
  "log_id": 1,
  "tasks_completed": 5,
  "tasks_total": 8
}
```

---

## 5. 反思与调整

### 5.1 运行反思

```
POST /api/v1/reflection/run
```

**请求体:**
```json
{
  "goal_id": 1,  // 可选，不填则反思所有任务
  "auto_apply": true  // 是否自动应用调整建议
}
```

**响应:** `ReflectionResultResponse`
```json
{
  "success": true,
  "reflection_log_id": 1,
  "analysis": {
    "overall_progress": "进展良好",
    "completion_trend": "上升趋势",
    "key_issues": ["时间分配不均"],
    "positive_aspects": ["坚持每天学习"]
  },
  "recommendations": {
    "task_adjustments": [...],
    "new_tasks": [...],
    "general_suggestions": ["建议早上学习"]
  },
  "summary": "整体表现良好，建议优化时间分配",
  "applied": true,
  "apply_result": {
    "adjusted_tasks": 3,
    "created_tasks": 2
  }
}
```

---

### 5.2 获取反思日志列表

```
GET /api/v1/reflection/logs
```

**查询参数:**
- `goal_id` - 过滤目标 ID
- `limit` - 返回数量 (默认 10，最大 50)

**响应:** `List<ReflectionLogResponse>`

---

### 5.3 获取单个反思日志

```
GET /api/v1/reflection/logs/{log_id}
```

**响应:** `ReflectionLogResponse`

---

### 5.4 应用反思调整

```
POST /api/v1/reflection/logs/{log_id}/apply
```

**响应:**
```json
{
  "success": true,
  "message": "Adjustments applied successfully",
  "apply_result": {
    "adjusted_tasks": 3,
    "created_tasks": 2
  }
}
```

---

## 6. 用户设置

### 6.1 获取当前用户信息

```
GET /api/v1/users/me
```

**响应:** `UserResponse`
```json
{
  "id": 1,
  "username": "john_doe",
  "push_token": "abc123...",
  "preferences": {
    "theme": "dark",
    "notification_enabled": true
  },
  "created_at": "2026-02-23T12:00:00Z"
}
```

---

### 6.2 更新推送 Token

```
POST /api/v1/users/push-token
```

**请求体:**
```json
{
  "push_token": "fcm_token_from_flutter_push"
}
```

**响应:**
```json
{
  "success": true,
  "message": "Push token updated successfully"
}
```

---

### 6.3 删除推送 Token

```
DELETE /api/v1/users/push-token
```

**响应:**
```json
{
  "success": true,
  "message": "Push token removed successfully"
}
```

---

### 6.4 更新用户偏好

```
PUT /api/v1/users/preferences
```

**请求体:**
```json
{
  "preferences": {
    "theme": "light",
    "notification_enabled": false,
    "language": "zh-CN"
  }
}
```

**响应:**
```json
{
  "success": true,
  "message": "Preferences updated successfully",
  "preferences": {...}
}
```

---

## 7. 错误处理

### 7.1 标准错误响应格式

```json
{
  "success": false,
  "error": "错误类型",
  "details": "详细错误信息"
}
```

### 7.2 常见 HTTP 状态码

| 状态码 | 含义 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 正常处理响应 |
| 201 | 创建成功 | 刷新列表或跳转 |
| 400 | 请求参数错误 | 检查输入并提示用户 |
| 401 | 未授权 | Token 过期，需重新登录 |
| 403 | 禁止访问 | 无权限，提示用户 |
| 404 | 资源不存在 | 刷新或返回上一页 |
| 500 | 服务器错误 | 稍后重试，显示友好提示 |

---

### 7.3 Flutter 错误处理示例

```dart
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  
  ApiException(this.message, {this.statusCode});
}

class ApiClient {
  final String baseUrl;
  String? _token;
  
  Future<Map<String, String>> get _headers async {
    final headers = {'Content-Type': 'application/json'};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }
  
  Future<dynamic> get(String path) async {
    final response = await http.get(
      Uri.parse('$baseUrl$path'),
      headers: await _headers,
    );
    
    if (response.statusCode == 401) {
      throw ApiException('Token expired', statusCode: 401);
    } else if (response.statusCode >= 400) {
      final error = jsonDecode(response.body);
      throw ApiException(error['details'] ?? error['error'], statusCode: response.statusCode);
    }
    
    return jsonDecode(response.body);
  }
  
  Future<dynamic> post(String path, Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: await _headers,
      body: jsonEncode(data),
    );
    
    // 同上错误处理...
    return jsonDecode(response.body);
  }
}
```

---

## 附录

### A. 数据模型

#### TaskStatus
- `pending` - 待完成
- `completed` - 已完成
- `skipped` - 已跳过

#### TaskPriority
- `0` - 低优先级
- `1` - 中优先级
- `2` - 高优先级

### B. 日期时间格式
- 日期：`YYYY-MM-DD` (e.g., `2026-02-23`)
- 时间：`HH:MM` (e.g., `14:00`)
- 日期时间：ISO 8601 (e.g., `2026-02-23T12:00:00Z`)

### C. 健康检查

```
GET /health
```

**响应:**
```json
{
  "status": "healthy",
  "message": "Plan Agent Backend is running"
}
```

---

## 8. 单词学习

### 8.1 获取单词设置

```
GET /api/v1/words/settings
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**响应:** `WordSettingsResponse`
```json
{
  "id": 1,
  "user_id": 1,
  "selected_tags": ["四级", "六级"],
  "daily_count": 10,
  "repeat_en": 2,
  "repeat_zh": 1,
  "enable_notification": true,
  "updated_at": "2026-02-25T08:00:00Z"
}
```

**说明:** 如果用户没有设置记录，返回默认值。

---

### 8.2 保存/更新单词设置

```
POST /api/v1/words/settings
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "selected_tags": ["四级"],  // 可选
  "daily_count": 20,           // 可选, 1-100
  "repeat_en": 3,               // 可选, 1-10
  "repeat_zh": 2,              // 可选, 1-10
  "enable_notification": false   // 可选
}
```

**响应:** `WordSettingsResponse`
```json
{
  "id": 1,
  "user_id": 1,
  "selected_tags": ["四级"],
  "daily_count": 20,
  "repeat_en": 3,
  "repeat_zh": 2,
  "enable_notification": false,
  "updated_at": "2026-02-25T08:30:00Z"
}
```

**错误:**
- 400: 未提供任何有效字段

---

### 8.3 获取每日单词任务

```
GET /api/v1/words/daily
```

**查询参数:**
- `date` - 日期 (YYYY-MM-DD格式，可选，默认当天)

**Headers:**
```
Authorization: Bearer <access_token>
```

**响应:** `DailyWordsResponse`
```json
{
  "task_id": 1,
  "task_date": "2026-02-25",
  "total_count": 10,
  "completed_count": 3,
  "status": "pending",
  "words": [
    {
      "id": 1,
      "word": "emperor",
      "translation": "皇帝；君主",
      "phonetic_us": "/ˈempərə(r)/",
      "phonetic_uk": "/ˈempərə(r)/",
      "part_of_speech": "n",
      "audio_url_en": "/audio/emperor_en.mp3",
      "audio_url_zh": "/audio/emperor_zh.mp3",
      "examples": null
    }
  ]
}
```

**错误:**
- 400: 用户未设置单词偏好，请先设置
- 404: 无法生成每日单词任务

---

### 8.4 标记单词完成

```
POST /api/v1/words/daily/complete
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "word_id": 123,
  "date": "2026-02-25"  // 可选，默认当天
}
```

**响应:** `WordCompleteResponse`
```json
{
  "completed": 5,
  "total": 10,
  "status": "pending"
}
```

**错误:**
- 400: 无效的单词ID / 今日任务已完成
- 404: 当天任务不存在

---

### 8.5 获取学习统计

```
GET /api/v1/words/stats
```

**查询参数:**
- `start_date` - 开始日期 (YYYY-MM-DD，可选，默认30天前)
- `end_date` - 结束日期 (YYYY-MM-DD，可选，默认当天)

**Headers:**
```
Authorization: Bearer <access_token>
```

**响应:** `WordStatsResponse`
```json
{
  "total_days": 15,
  "total_words_assigned": 150,
  "total_words_completed": 120,
  "completion_rate": 0.8,
  "daily_average": 8.0,
  "daily_details": [
    {
      "date": "2026-02-25",
      "total_words": 10,
      "completed_words": 10,
      "status": "completed"
    },
    {
      "date": "2026-02-24",
      "total_words": 10,
      "completed_words": 8,
      "status": "pending"
    }
  ]
}
```

---

### 8.6 提交功能反馈

```
POST /api/v1/feedback
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**请求体:**
```json
{
  "feature_name": "word_follow",
  "feedback_type": "suggestion",  // suggestion, bug, praise
  "content": "希望增加例句显示",
  "rating": 4  // 可选, 1-5
}
```

**响应:** `FeedbackResponse`
```json
{
  "success": true,
  "id": 1
}
```

---

### 8.7 数据模型

#### WordSettingsResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 设置ID |
| user_id | int | 用户ID |
| selected_tags | List[str] | 选择的标签 |
| daily_count | int | 每日学习数量 |
| repeat_en | int | 英文重复次数 |
| repeat_zh | int | 中文重复次数 |
| enable_notification | bool | 是否启用通知 |
| updated_at | datetime | 更新时间 |

#### DailyWordsResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | int | 任务ID |
| task_date | date | 任务日期 |
| total_count | int | 单词总数 |
| completed_count | int | 已完成数量 |
| status | str | pending/completed |
| words | List[WordDetail] | 单词详情列表 |

#### WordDetail
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 单词ID |
| word | str | 单词 |
| translation | str | 翻译 |
| phonetic_us | str? | 美式音标 |
| phonetic_uk | str? | 英式音标 |
| part_of_speech | str? | 词性 |
| audio_url_en | str? | 英文音频URL |
| audio_url_zh | str? | 中文音频URL |
| examples | List[dict]? | 例句 |

#### WordStatsResponse
| 字段 | 类型 | 说明 |
|------|------|------|
| total_days | int | 学习天数 |
| total_words_assigned | int | 分配单词总数 |
| total_words_completed | int | 完成单词总数 |
| completion_rate | float | 完成率 |
| daily_average | float | 日均完成数 |
| daily_details | List[DailyStat] | 每日详情 |

---

**文档版本:** v1.0.0  
**最后更新:** 2026-02-25  
**项目:** Plan Agent Backend  
**技术栈:** FastAPI + SQLAlchemy + PostgreSQL + OpenAI
