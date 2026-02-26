# AGENTS.md - 代码库开发指南

> **重要提示**：本文件旨在为 AI 代理提供在本代码库中工作的完整指南。  
> 包含构建命令、代码风格约定、测试方法和项目特定模式。

## 📋 项目概述

本代码库包含两个独立项目：

1. **plan_agent_backend** - FastAPI 后端服务 (Python)
   - 智能任务规划与 AI 代理系统
   - FastAPI + SQLAlchemy + PostgreSQL + Pydantic
   - 提供 RESTful API 供 Flutter 前端使用

2. **plan_ai_flutter** - Flutter 移动/Web 应用 (Dart)
   - 跨平台任务管理与学习助手
   - Flutter + Provider 状态管理
   - 支持 Android、iOS、Web、Windows

---

## 🔧 后端项目 - Plan Agent Backend

### 构建与运行命令

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 数据库迁移
# 初始化数据库 (首次运行)
python init_db.py

# 创建新迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 3. 启动开发服务器
# 方式1: 使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2: 使用脚本 (如有)
python -m app.main

# 4. 健康检查
curl http://localhost:8000/health
```

### 代码风格指南

#### 导入顺序
```python
# 1. 标准库
from datetime import datetime, timedelta
from typing import List, Optional

# 2. 第三方库
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 3. 项目内部模块
from app.config import settings
from app.schemas import UserCreate, UserResponse
```

#### 命名约定
- **类名**: `PascalCase` (如 `AuthProvider`, `TaskService`)
- **函数名**: `snake_case` (如 `get_current_user`, `create_access_token`)
- **变量名**: `snake_case` (如 `user_data`, `access_token`)
- **常量**: `UPPER_SNAKE_CASE` (如 `API_PREFIX`, `JWT_SECRET_KEY`)

#### Pydantic 模型规范
```python
from pydantic import BaseModel, Field, field_validator

class TaskCreate(BaseModel):
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    priority: Optional[int] = Field(default=1, description="Task priority (0/1/2)")
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: int) -> int:
        if v not in [0, 1, 2]:
            raise ValueError('Priority must be 0, 1, or 2')
        return v
```

#### FastAPI 路由模式
```python
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 业务逻辑
    pass
```

#### 错误处理模式
- 使用自定义异常类 (`AppException` 继承体系)
- 所有异常统一在 `app/exceptions.py` 中定义
- HTTP 错误码映射在 `ErrorCode` 枚举中
- 错误响应格式: `{"success": false, "error": "message", "error_code": "ERR_CODE"}`

### 数据库与迁移
- **ORM**: SQLAlchemy 2.0+ (`app/models.py`)
- **迁移工具**: Alembic (`alembic.ini`, `alembic/`)
- **数据库**: PostgreSQL (默认连接: `postgresql://postgres:postgres@localhost:5432/plan_agent_db`)

### 项目结构
```
plan_agent_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理 (Pydantic Settings)
│   ├── models.py            # SQLAlchemy 模型
│   ├── schemas.py           # Pydantic 模型 (请求/响应)
│   ├── exceptions.py        # 自定义异常
│   ├── dependencies.py      # FastAPI 依赖项
│   ├── logging_config.py    # 日志配置
│   ├── scheduler.py         # 定时任务
│   ├── routers/             # API 路由
│   │   ├── auth.py          # 认证路由
│   │   ├── tasks.py         # 任务管理
│   │   ├── words.py         # 单词学习
│   │   └── ...
│   ├── services/            # 业务逻辑层
│   │   ├── word_service.py  # 单词服务
│   │   ├── ai_service.py    # AI 服务
│   │   └── ...
│   ├── agent/               # AI Agent 系统
│   │   ├── router.py        # Agent 路由
│   │   ├── types.py         # Agent 类型定义
│   │   └── tools/           # Agent 工具
│   └── utils/               # 工具函数
├── alembic/                 # 数据库迁移
├── word_format/             # 单词数据
├── requirements.txt         # Python 依赖
├── alembic.ini             # Alembic 配置
├── .env.example            # 环境变量示例
├── init_db.py              # 数据库初始化
└── import_words.py         # 单词数据导入
```

---

## 📱 Flutter 项目 - Plan AI Flutter

### 构建与运行命令

```bash
# 1. 获取依赖
flutter pub get

# 2. 代码分析
flutter analyze

# 3. 运行应用
flutter run                # 选择目标设备
flutter run -d chrome      # Web 浏览器
flutter run -d windows     # Windows 桌面

# 4. 构建发布版本
flutter build apk         # Android APK
flutter build web         # Web 应用
flutter build windows     # Windows 可执行文件

# 5. 运行测试
flutter test              # 运行所有测试
flutter test test/widget_test.dart  # 运行单个测试
flutter test --reporter expanded    # 详细输出
```

### 代码风格指南

#### 导入顺序
```dart
// 1. Flutter SDK
import 'package:flutter/material.dart';

// 2. 第三方包
import 'package:provider/provider.dart';
import 'package:http/http.dart';

// 3. 项目内部
import '../providers/auth_provider.dart';
import '../models/user.dart';
import '../utils/constants.dart';
```

#### 命名约定
- **类名**: `PascalCase` (如 `AuthProvider`, `HomeScreen`)
- **文件名**: `snake_case.dart` (如 `auth_provider.dart`, `home_screen.dart`)
- **函数名**: `camelCase` (如 `loginUser`, `fetchTasks`)
- **私有成员**: `_underscorePrefix` (如 `_isLoading`, `_fetchData`)
- **常量**: `PascalCase` (如 `ApiConstants`, `StorageKeys`)

#### Widget 规范
```dart
// 1. 屏幕组件 (StatefulWidget)
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('主页')),
      body: const Center(child: Text('欢迎使用 Plan AI')),
    );
  }
}

// 2. 无状态组件 (StatelessWidget)
class TaskItem extends StatelessWidget {
  const TaskItem({super.key, required this.task});
  
  final Task task;
  
  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(task.title),
      subtitle: Text(task.description ?? ''),
    );
  }
}
```

#### 状态管理 (Provider)
```dart
class AuthProvider extends ChangeNotifier {
  AuthStatus _status = AuthStatus.unknown;
  User? _user;
  
  AuthStatus get status => _status;
  User? get user => _user;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  
  Future<void> login(String username, String password) async {
    try {
      _status = AuthStatus.loading;
      notifyListeners();
      
      final user = await ApiService.login(username, password);
      _user = user;
      _status = AuthStatus.authenticated;
    } catch (e) {
      _status = AuthStatus.unauthenticated;
      rethrow;
    } finally {
      notifyListeners();
    }
  }
}
```

#### 错误处理
```dart
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  
  ApiException(this.message, {this.statusCode});
}

// 使用示例
try {
  final response = await http.get(uri, headers: headers);
  if (response.statusCode == 401) {
    throw ApiException('Token expired', statusCode: 401);
  }
} on ApiException catch (e) {
  // 处理 API 错误
} catch (e) {
  // 处理其他错误
}
```

#### Model 规范 (JSON 序列化)
```dart
class Task {
  final int id;
  final String title;
  final String? description;
  final TaskStatus status;
  final DateTime createdAt;
  
  Task({
    required this.id,
    required this.title,
    this.description,
    required this.status,
    required this.createdAt,
  });
  
  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      status: TaskStatus.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => TaskStatus.pending,
      ),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'status': status.name,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
```

### 项目结构
```
plan_ai_flutter/
├── lib/
│   ├── main.dart                    # 应用入口
│   ├── providers/                   # Provider 状态管理
│   │   └── auth_provider.dart
│   ├── services/                    # API 服务层
│   │   └── api_service.dart
│   ├── models/                      # 数据模型
│   │   ├── user.dart
│   │   ├── task.dart
│   │   ├── goal.dart
│   │   ├── comment.dart
│   │   ├── reflection.dart
│   │   └── fixed_schedule.dart
│   ├── screens/                     # UI 屏幕 (13个)
│   │   ├── home_screen.dart
│   │   ├── login_screen.dart
│   │   ├── register_screen.dart
│   │   ├── tasks_screen.dart
│   │   ├── task_detail_screen.dart
│   │   ├── goals_screen.dart
│   │   ├── goal_detail_screen.dart
│   │   ├── schedule_screen.dart
│   │   ├── friends_screen.dart
│   │   ├── friend_tasks_screen.dart
│   │   ├── features_screen.dart
│   │   ├── ai_plan_screen.dart
│   │   └── word_*.dart             # 单词学习相关
│   └── utils/
│       └── constants.dart           # API 常量和存储键
├── test/
│   └── widget_test.dart            # 测试示例
├── android/, ios/, windows/, web/  # 平台配置
├── pubspec.yaml                    # 项目配置
├── analysis_options.yaml           # 代码分析规则
├── .metadata                      # Flutter 项目元数据
└── .env.example                   # 环境变量示例
```

---

## 🎯 通用开发约定

### 环境配置
- 后端: 复制 `.env.example` 为 `.env` 并配置环境变量
- Flutter: 复制 `.env.example` 为 `plan_ai_flutter/.env`
- **重要**: 不要将包含敏感信息的 `.env` 文件提交到版本控制

### 提交规范
- 提交信息使用中文或英文，清晰描述变更内容
- 功能提交: `feat: 添加单词学习功能`
- 修复提交: `fix: 修复登录 token 过期问题`
- 文档提交: `docs: 更新 API 文档`

### API 约定
- **后端 API 前缀**: `/api/v1`
- **认证**: Bearer Token (JWT)
- **日期格式**: `YYYY-MM-DD` (如 `2026-02-25`)
- **时间格式**: `HH:MM` (如 `14:00`)
- **错误响应**: 统一使用 `{"success": false, "error": "...", "error_code": "..."}`

### 多语言支持
- 后端: 中文错误消息，支持国际化扩展
- Flutter: 中文界面，使用 `AppLocalizations` 支持多语言

---

## 📝 注意事项

1. **类型安全**: 优先使用类型注解，避免 `dynamic` 类型
2. **异步处理**: 正确处理 `async/await` 和错误处理
3. **安全性**: 验证用户输入，使用参数化查询防止 SQL 注入
4. **性能**: 避免 N+1 查询，合理使用缓存
5. **测试**: 编写单元测试和集成测试，确保功能稳定

---

## 🔍 快速参考

### 后端快速启动
```bash
# 设置环境
cp .env.example .env
# 编辑 .env 文件配置数据库和 API Key

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Flutter 快速启动
```bash
# 设置环境
cd plan_ai_flutter
cp .env.example .env
# 编辑 .env 文件配置 API 地址

# 获取依赖
flutter pub get

# 运行应用
flutter run
```

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-25  
**维护者**: AI Agent Development Team  

> **提示**: 开发时请严格遵循本指南中的约定，确保代码质量和团队协作效率。