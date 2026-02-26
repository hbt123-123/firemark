# 云服务器测试指南

> 本文档详细介绍如何在云服务器上对 Plan Agent 项目进行全面测试。  
> 涵盖后端服务测试、Flutter 应用测试、API 接口测试、性能测试等。  
> 测试时若使用到APIkey，相关配置如：
  - API-key:sk-41cb17b852ea48aebeb8bfd1762d758c
  - url:https://dashscope.aliyuncs.com/compatible-mode/v1
  - 模型：
    - qwen3.5-plus-2026-02-15
    - text-embedding-v4
> 注意：由于测试项目，所以firemark/plan_agent_backend/word_format目录下的音频文件仅放置了几个测试音频，不影响最终项目结果。
> **版本**: v1.0.0 | **更新日期**: 2026-02-25

---

## 📋 目录

1. [测试前准备](#1-测试前准备)
2. [后端服务测试](#2-后端服务测试)
3. [API 接口测试](#3-api-接口测试)
4. [Flutter 应用测试](#4-flutter-应用测试)
5. [数据库测试](#5-数据库测试)
6. [AI Agent 系统测试](#6-ai-agent-系统测试)
7. [性能测试](#7-性能测试)
8. [安全测试](#8-安全测试)
9. [日志与监控测试](#9-日志与监控测试)
10. [常见问题排查](#10-常见问题排查)

---

## 1. 测试前准备

### 1.1 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 40 GB | 100 GB SSD |
| 系统 | Ubuntu 20.04+ / CentOS 8+ | Ubuntu 22.04 LTS |

### 1.2 依赖服务检查

```bash
# 检查 PostgreSQL 服务状态
sudo systemctl status postgresql

# 检查 Redis 服务状态
sudo systemctl status redis

# 检查系统资源
free -h           # 内存使用情况
df -h             # 磁盘使用情况
nproc             # CPU 核心数
```

### 1.3 网络端口检查

```bash
# 检查端口占用情况
sudo netstat -tlnp | grep -E ':(8000|5432|6379)'

# 确保防火墙开放必要端口
sudo ufw allow 8000/tcp  # 后端 API
sudo ufw allow 80/tcp    # Web 应用
sudo ufw allow 443/tcp   # HTTPS
```

### 1.4 代码部署检查

```bash
# 确认代码已部署到服务器
ls -la /opt/plan_agent/

# 检查 Python 环境
python3 --version
pip3 --version

# 检查 Node.js 环境 (如有前端)
node --version
npm --version

# 检查 Flutter 环境 (如需构建)
flutter --version
```

---

## 2. 后端服务测试

### 2.1 服务启动测试

#### 方式一：直接运行（开发模式）

```bash
# 进入后端目录
cd /opt/plan_agent/plan_agent_backend

# 激活虚拟环境
source venv/bin/activate

# 启动服务（前台运行，查看日志）
python -m app.main

# 或使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 方式二：系统服务（生产模式）

```bash
# 创建 systemd 服务文件
sudo nano /etc/systemd/system/plan-agent.service
```

服务配置内容：

```ini
[Unit]
Description=Plan Agent Backend Service
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/plan_agent/plan_agent_backend
Environment="PATH=/opt/plan_agent/plan_agent_backend/venv/bin"
ExecStart=/opt/plan_agent/plan_agent_backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable plan-agent
sudo systemctl start plan-agent

# 查看服务状态
sudo systemctl status plan-agent

# 查看实时日志
journalctl -u plan-agent -f
```

### 2.2 健康检查测试

```bash
# 基础健康检查
curl -s http://localhost:8000/health

# 预期返回：
# {"status":"healthy","message":"Plan Agent Backend is running"}

# 带详细信息的健康检查（如果已实现）
curl -s http://localhost:8000/health/detailed | python3 -m json.tool
```

### 2.3 服务响应测试

```bash
# 测试 API 响应时间
time curl -s http://localhost:8000/health

# 测试并发请求
for i in {1..100}; do
  curl -s http://localhost:8000/health > /dev/null &
done
wait

echo "并发测试完成"
```

### 2.4 后端日志测试

```bash
# 查看应用日志
tail -f /var/log/plan_agent/app.log

# 查看 uvicorn 日志
tail -f /var/log/plan_agent/uvicorn.log

# 查看错误日志
grep -i error /var/log/plan_agent/app.log | tail -50
```

---

## 3. API 接口测试

### 3.1 认证接口测试

#### 用户注册

```bash
# 测试用户注册 - 成功案例
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"Test123456"}'

# 预期返回（201 Created）：
# {"id":1,"username":"testuser001","created_at":"2026-02-25T10:00:00Z"}

# 测试用户注册 - 用户名已存在（400 Bad Request）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"Test123456"}'

# 预期返回：
# {"success":false,"error":"Username already registered","error_code":"ERR_AUTH_001"}

# 测试用户注册 - 用户名过短（422 Unprocessable Entity）
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ab","password":"Test123456"}'
```

#### 用户登录

```bash
# 测试登录 - 成功
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"Test123456"}'

# 预期返回：
# {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}

# 测试登录 - 密码错误（401 Unauthorized）
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"WrongPassword"}'

# 测试登录 - 用户不存在（401 Unauthorized）
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"nonexistent","password":"Test123456"}'

# 测试表单登录
curl -X POST http://localhost:8000/api/v1/auth/login/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser001&password=Test123456"
```

#### Token 验证

```bash
# 获取 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"Test123456"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 测试获取当前用户信息
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 测试 Token 过期
# 等待 Token 过期或使用过期 Token 测试
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer expired_token_here"

# 预期返回：
# {"success":false,"error":"登录已过期，请重新登录","error_code":"ERR_AUTH_003"}
```

### 3.2 任务管理接口测试

```bash
# 设置认证 Token
TOKEN="your_access_token_here"

# 创建任务 - 成功
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "学习 Python 基础",
    "description": "完成 Python 入门教程",
    "due_date": "2026-02-28",
    "due_time": "14:00",
    "priority": 1
  }'

# 获取任务列表
curl -X GET "http://localhost:8000/api/v1/tasks?status=pending&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# 获取今日任务
curl -X GET http://localhost:8000/api/v1/tasks/today \
  -H "Authorization: Bearer $TOKEN"

# 获取单个任务
curl -X GET http://localhost:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TOKEN"

# 更新任务
curl -X PUT http://localhost:8000/api/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "更新后的标题","priority":2}'

# 完成任务
curl -X POST http://localhost:8000/api/v1/tasks/1/complete \
  -H "Authorization: Bearer $TOKEN"

# 跳过任务
curl -X POST http://localhost:8000/api/v1/tasks/1/skip \
  -H "Authorization: Bearer $TOKEN"

# 删除任务
curl -X DELETE http://localhost:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer $TOKEN"

# 批量更新状态
curl -X POST "http://localhost:8000/api/v1/tasks/batch-update-status?status=completed" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '[1,2,3]'
```

### 3.3 目标管理接口测试

```bash
TOKEN="your_access_token_here"

# 创建目标
curl -X POST http://localhost:8000/api/v1/goals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Python 学习计划",
    "description": "三个月掌握 Python 基础",
    "start_date": "2026-02-01",
    "end_date": "2026-05-01",
    "objective_topic": "Python 编程",
    "objective_criterion": "能够独立完成小型项目"
  }'

# 获取目标列表
curl -X GET http://localhost:8000/api/v1/goals \
  -H "Authorization: Bearer $TOKEN"

# 获取目标详情
curl -X GET http://localhost:8000/api/v1/goals/1 \
  -H "Authorization: Bearer $TOKEN"

# 更新目标
curl -X PUT http://localhost:8000/api/v1/goals/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"status":"completed"}'

# 删除目标
curl -X DELETE http://localhost:8000/api/v1/goals/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 3.4 AI Agent 接口测试

```bash
TOKEN="your_access_token_here"

# 智能对话 - 创建计划
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "我想学习 Python，请帮我制定一个学习计划",
    "session_id": "session_test_001"
  }'

# 智能对话 - 调整任务
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "我每天只能学习 2 小时，请调整计划",
    "session_id": "session_test_001"
  }'

# 获取可用插件
curl -X GET http://localhost:8000/api/v1/agent/plugins \
  -H "Authorization: Bearer $TOKEN"

# 直接执行 Skill
curl -X POST http://localhost:8000/api/v1/agent/skill \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "skill_name": "generate_plan",
    "parameters": {
      "goal_id": 1,
      "additional_context": "我希望每天学习 2 小时"
    }
  }'

# 清除会话
curl -X DELETE http://localhost:8000/api/v1/agent/session/session_test_001 \
  -H "Authorization: Bearer $TOKEN"
```

### 3.5 单词学习接口测试

```bash
TOKEN="your_access_token_here"

# 获取单词设置
curl -X GET http://localhost:8000/api/v1/words/settings \
  -H "Authorization: Bearer $TOKEN"

# 保存单词设置
curl -X POST http://localhost:8000/api/v1/words/settings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "selected_tags": ["四级","考研"],
    "daily_count": 20,
    "repeat_en": 3,
    "repeat_zh": 2,
    "enable_notification": true
  }'

# 获取每日单词
curl -X GET http://localhost:8000/api/v1/words/daily \
  -H "Authorization: Bearer $TOKEN"

# 获取指定日期单词
curl -X GET "http://localhost:8000/api/v1/words/daily?date=2026-02-25" \
  -H "Authorization: Bearer $TOKEN"

# 标记单词完成
curl -X POST http://localhost:8000/api/v1/words/daily/complete \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"word_id": 1, "date": "2026-02-25"}'

# 获取学习统计
curl -X GET http://localhost:8000/api/v1/words/stats \
  -H "Authorization: Bearer $TOKEN"

# 获取指定时间段统计
curl -X GET "http://localhost:8000/api/v1/words/stats?start_date=2026-01-01&end_date=2026-02-25" \
  -H "Authorization: Bearer $TOKEN"
```

### 3.6 执行跟踪接口测试

```bash
TOKEN="your_access_token_here"

# 获取执行日志列表
curl -X GET http://localhost:8000/api/v1/execution/logs \
  -H "Authorization: Bearer $TOKEN"

# 获取指定日期范围日志
curl -X GET "http://localhost:8000/api/v1/execution/logs?start_date=2026-02-01&end_date=2026-02-25" \
  -H "Authorization: Bearer $TOKEN"

# 获取单日执行日志
curl -X GET http://localhost:8000/api/v1/execution/logs/2026-02-25 \
  -H "Authorization: Bearer $TOKEN"

# 获取执行统计
curl -X GET "http://localhost:8000/api/v1/execution/stats?start_date=2026-01-01&end_date=2026-02-25" \
  -H "Authorization: Bearer $TOKEN"

# 更新执行反馈
curl -X POST http://localhost:8000/api/v1/execution/logs/2026-02-25/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "difficulties": "今天工作太忙",
    "feedback": "明天需要早起学习"
  }'

# 生成每日日志
curl -X POST http://localhost:8000/api/v1/execution/logs/generate?log_date=2026-02-25 \
  -H "Authorization: Bearer $TOKEN"
```

### 3.7 反思系统接口测试

```bash
TOKEN="your_access_token_here"

# 运行反思
curl -X POST http://localhost:8000/api/v1/reflection/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "goal_id": 1,
    "auto_apply": true
  }'

# 获取反思日志列表
curl -X GET "http://localhost:8000/api/v1/reflection/logs?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# 获取单个反思日志
curl -X GET http://localhost:8000/api/v1/reflection/logs/1 \
  -H "Authorization: Bearer $TOKEN"

# 应用反思调整
curl -X POST http://localhost:8000/api/v1/reflection/logs/1/apply \
  -H "Authorization: Bearer $TOKEN"
```

### 3.8 接口响应时间测试

```bash
# 测试各接口响应时间
echo "=== 接口响应时间测试 ==="

echo -n "健康检查: "
time curl -s http://localhost:8000/health > /dev/null

echo -n "登录: "
time curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"Test123456"}' > /dev/null

echo -n "获取任务列表: "
time curl -s -X GET http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" > /dev/null

echo -n "AI 对话: "
time curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"你好"}' > /dev/null
```

---

## 4. Flutter 应用测试

### 4.1 开发环境构建测试

```bash
# 进入 Flutter 项目目录
cd /opt/plan_agent/plan_ai_flutter

# 获取依赖
flutter pub get

# 运行代码分析
flutter analyze

# 运行应用（调试模式）
flutter run -d chrome
flutter run -d windows

# 构建 Web 版本
flutter build web --release

# 构建 Windows 版本
flutter build windows --release

# 构建 Android APK（在有 Android SDK 的环境中）
flutter build apk --debug
flutter build apk --release
```

### 4.2 生产环境构建测试

```bash
# 清理构建缓存
flutter clean

# 重新获取依赖
flutter pub get

# Web 构建
flutter build web --release --web-renderer html

# 检查构建产物
ls -la build/web/
ls -la build/windows/x64/release/

# Windows 发布构建
flutter build windows --release
```

### 4.3 Flutter 测试套件

```bash
# 运行所有测试
flutter test

# 运行特定测试文件
flutter test test/widget_test.dart

# 运行测试并显示详细输出
flutter test --reporter expanded

# 运行测试并生成覆盖率报告
flutter test --coverage

# 查看覆盖率报告
genhtml coverage/lcov.info -o coverage/html
```

### 4.4 特定平台测试

```bash
# Linux 桌面测试
flutter test -d linux

# macOS 测试（仅在 macOS 上）
flutter test -d macos

# Windows 桌面测试
flutter test -d windows

# Chrome Web 测试
flutter test -d chrome
```

---

## 5. 数据库测试

### 5.1 数据库连接测试

```bash
# 登录 PostgreSQL
sudo -u postgres psql -d plan_agent_db

# 或使用应用配置的用户
psql -h localhost -U postgres -d plan_agent_db

# 测试连接
\conninfo

# 退出
\q
```

### 5.2 数据库表结构测试

```sql
-- 查看所有表
\dt

-- 查看用户表结构
\d users

-- 查看任务表结构
\d tasks

-- 查看目标表结构
\d goals

-- 查看单词表结构
\d words

-- 测试查询
SELECT * FROM users LIMIT 5;
SELECT COUNT(*) FROM tasks;
SELECT COUNT(*) FROM goals;
```

### 5.3 数据库性能测试

```sql
-- 开启查询计时
\timing on

-- 测试查询性能
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 1 AND status = 'pending';

-- 测试索引使用情况
EXPLAIN SELECT * FROM tasks WHERE due_date = '2026-02-25';

-- 测试连接查询
EXPLAIN ANALYZE 
SELECT t.*, g.title as goal_title 
FROM tasks t 
LEFT JOIN goals g ON t.goal_id = g.id 
WHERE t.user_id = 1;
```

### 5.4 数据库备份与恢复测试

```bash
# 备份数据库
pg_dump -h localhost -U postgres -d plan_agent_db > /backup/plan_agent_$(date +%Y%m%d).sql

# 压缩备份
pg_dump -h localhost -U postgres -d plan_agent_db | gzip > /backup/plan_agent_$(date +%Y%m%d).sql.gz

# 恢复数据库
psql -h localhost -U postgres -d plan_agent_db < /backup/plan_agent_20260225.sql

# 测试定时备份
crontab -e
# 添加：0 2 * * * /opt/plan_agent/scripts/backup.sh
```

---

## 6. AI Agent 系统测试

### 6.1 Agent 基础功能测试

```bash
TOKEN="your_access_token_here"

# 测试不同类型的用户意图
echo "=== 测试创建计划意图 ==="
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"帮我制定一个月的学习计划"}'

echo "=== 测试调整任务意图 ==="
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"任务太多了，请减少一些"}'

echo "=== 测试查询意图 ==="
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"我今天完成了哪些任务？"}'

echo "=== 测试闲聊 ==="
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"你好"}'
```

### 6.2 Agent 记忆系统测试

```bash
TOKEN="your_access_token_here"

# 创建会话并多次对话，测试记忆保持
SESSION_ID="session_memory_test_001"

# 第一次对话
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\":\"我叫张三\",\"session_id\":\"$SESSION_ID\"}"

# 第二次对话（测试记忆）
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\":\"你知道我叫什么吗？\",\"session_id\":\"$SESSION_ID\"}"

# 清除会话
curl -s -X DELETE http://localhost:8000/api/v1/agent/session/$SESSION_ID \
  -H "Authorization: Bearer $TOKEN"
```

### 6.3 Agent 错误处理测试

```bash
TOKEN="your_access_token_here"

# 测试空消息
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":""}'

# 测试超长消息
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"message\":\"$LONG_MESSAGE\"}"

# 测试无效会话
curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"测试","session_id":"invalid_session_xxx"}'
```

---

## 7. 性能测试

### 7.1 基础负载测试

```bash
# 安装负载测试工具
sudo apt-get install -y apache2-utils

# 基础压力测试（100 个请求）
ab -n 100 -c 10 http://localhost:8000/health

# 认证接口压力测试
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser001","password":"Test123456"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tasks
```

### 7.2 并发连接测试

```bash
# 测试 WebSocket 连接（如果有）
# 安装 wscat
npm install -g wscat

# 测试 WebSocket 连接
wscat -c ws://localhost:8000/ws

# 使用 wrk 进行 HTTP 压力测试
# 安装 wrk
sudo apt-get install -y wrk

# 高级压力测试
wrk -t12 -c400 -d30s http://localhost:8000/health
```

### 7.3 数据库性能测试

```sql
-- PostgreSQL 性能监控
-- 开启性能统计
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';

-- 重启 PostgreSQL 后执行
SELECT pg_stat_statements_reset();

-- 执行查询后查看统计
SELECT query, calls, total_time, rows 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

### 7.4 内存和 CPU 使用测试

```bash
# 监控进程资源使用
top -p $(pgrep -f "uvicorn")

# 持续监控
pidstat -p $(pgrep -f "uvicorn") 1

# 监控内存使用
ps aux | grep uvicorn | grep -v grep

# 查看打开的文件描述符
lsof -p $(pgrep -f "uvicorn") | wc -l
```

---

## 8. 安全测试

### 8.1 认证安全测试

```bash
# 测试 SQL 注入
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin\" OR 1=1--","password":"anything"}'

# 测试 XSS（应被过滤）
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"<script>alert(1)</script>","due_date":"2026-02-28"}'

# 测试越权访问
curl -X GET http://localhost:8000/api/v1/tasks/99999 \
  -H "Authorization: Bearer $TOKEN"

# 测试 Token 猜测
for i in {1..100}; do
  TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9$(echo $i | base64)"
  curl -s -X GET http://localhost:8000/api/v1/auth/me \
    -H "Authorization: Bearer $TOKEN" | grep -q "success" && echo "Found valid token at $i"
done
```

### 8.2 速率限制测试

```bash
# 测试登录接口速率限制
for i in {1..20}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"rate_test","password":"wrong"}'
done

# 预期：部分请求返回 429 Too Many Requests
```

### 8.3 CORS 安全测试

```bash
# 测试跨域请求
curl -s -I http://localhost:8000/api/v1/health \
  -H "Origin: http://malicious-site.com"

# 预期响应头应包含：
# Access-Control-Allow-Origin: http://localhost:3000
# 不应为：Access-Control-Allow-Origin: *
```

### 8.4 敏感数据测试

```bash
# 测试密码返回
curl -s -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" | grep -i password

# 预期：不应返回 password_hash 等敏感字段

# 测试日志中的敏感信息
grep -r "password" /var/log/plan_agent/
grep -r "token" /var/log/plan_agent/ | grep -v "access_token"
```

---

## 9. 日志与监控测试

### 9.1 日志输出测试

```bash
# 检查应用日志是否正常写入
tail -f /var/log/plan_agent/app.log

# 检查不同级别的日志
grep -i "error" /var/log/plan_agent/app.log | tail -20
grep -i "warning" /var/log/plan_agent/app.log | tail -20
grep -i "info" /var/log/plan_agent/app.log | tail -20

# 检查 JSON 格式日志（结构化日志）
cat /var/log/plan_agent/app.log | python3 -m json.tool
```

### 9.2 日志轮转测试

```bash
# 检查日志轮转配置
cat /etc/logrotate.d/plan-agent

# 手动触发日志轮转
logrotate -f /etc/logrotate.d/plan-agent

# 检查轮转后的日志
ls -la /var/log/plan_agent/
```

### 9.3 Prometheus 指标测试（如果已配置）

```bash
# 测试 Prometheus 指标端点
curl -s http://localhost:8000/metrics

# 测试特定指标
curl -s http://localhost:8000/metrics | grep "http_requests_total"
curl -s http://localhost:8000/metrics | grep "api_response_time"
```

### 9.4 健康检查端点测试

```bash
# 基础健康检查
curl -s http://localhost:8000/health

# 详细健康检查（如果实现）
curl -s http://localhost:8000/health/detailed | python3 -m json.tool

# 测试健康检查在故障时的响应
# 停止数据库后
curl -s http://localhost:8000/health
# 预期：返回 unhealthy 状态
```

---

## 10. 常见问题排查

### 10.1 服务无法启动

```bash
# 检查端口占用
sudo netstat -tlnp | grep 8000

# 检查进程状态
ps aux | grep uvicorn

# 检查日志中的错误
tail -100 /var/log/plan_agent/app.log | grep -i error

# 检查 Python 依赖
cd /opt/plan_agent/plan_agent_backend
source venv/bin/activate
pip list | grep -E "(fastapi|sqlalchemy|pydantic)"

# 检查数据库连接
python3 -c "from app.database import engine; engine.connect()"
```

### 10.2 API 返回 500 错误

```bash
# 查看详细错误日志
tail -f /var/log/plan_agent/app.log

# 开启调试模式
# 编辑 .env 文件
DEBUG=True

# 重启服务
sudo systemctl restart plan-agent

# 复现问题并查看详细错误
curl -v http://localhost:8000/api/v1/tasks
```

### 10.3 数据库连接问题

```bash
# 检查 PostgreSQL 服务
sudo systemctl status postgresql

# 检查数据库是否存在
sudo -u postgres psql -l | grep plan_agent_db

# 检查连接配置
cat /opt/plan_agent/plan_agent_backend/.env | grep DATABASE

# 测试数据库连接
psql -h localhost -U postgres -d plan_agent_db -c "SELECT 1;"

# 检查数据库连接数
sudo -u postgres psql -d plan_agent_db -c "SELECT count(*) FROM pg_stat_activity;"
```

### 10.4 内存泄漏问题

```bash
# 监控内存使用变化
while true; do
  echo "$(date +%H:%M:%S) - $(ps aux | grep uvicorn | grep -v grep | awk '{print $6}') KB"
  sleep 10
done

# 使用 valgrind 检测 Python 内存泄漏
# （需要安装 python-valgrind 或使用其他工具）
```

### 10.5 AI Agent 响应缓慢

```bash
# 检查 LLM API 响应时间
time curl -s -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"你好"}'

# 检查 LLM API Key 配置
cat /opt/plan_agent/plan_agent_backend/.env | grep LLM

# 测试 LLM API 直连
curl -s https://api.openai.com/v1/models \
  -H "Authorization: Bearer $LLM_API_KEY"
```

---

## 📋 测试检查清单

### 部署前检查
- [ ] 服务器环境符合要求
- [ ] 所有依赖服务运行正常
- [ ] 代码已正确部署
- [ ] 配置文件已正确设置
- [ ] 防火墙端口已开放

### 功能测试
- [ ] 用户注册/登录功能正常
- [ ] JWT Token 验证正常
- [ ] 任务 CRUD 操作正常
- [ ] 目标管理功能正常
- [ ] AI Agent 对话功能正常
- [ ] 单词学习功能正常
- [ ] 执行跟踪功能正常
- [ ] 反思系统功能正常

### 性能测试
- [ ] API 响应时间符合要求（< 200ms）
- [ ] 并发处理能力满足需求
- [ ] 数据库查询性能正常
- [ ] 内存和 CPU 使用正常

### 安全测试
- [ ] SQL 注入防护正常
- [ ] XSS 防护正常
- [ ] 越权访问防护正常
- [ ] 速率限制正常
- [ ] CORS 配置正确

### 日志监控测试
- [ ] 日志正常写入
- [ ] 日志轮转正常
- [ ] 健康检查端点正常
- [ ] 监控指标正常（如果配置）

---

## 🔧 自动化测试脚本

### 3.1 一键健康检查脚本

```bash
#!/bin/bash
# health_check.sh

echo "=== Plan Agent 健康检查 ==="
echo ""

# 检查服务状态
echo "1. 检查服务状态..."
systemctl is-active --quiet plan-agent && echo "✓ 后端服务运行中" || echo "✗ 后端服务未运行"

# 检查端口
echo "2. 检查端口..."
netstat -tln | grep -q :8000 && echo "✓ 8000 端口监听中" || echo "✗ 8000 端口未监听"

# 检查数据库连接
echo "3. 检查数据库..."
pg_isready -h localhost -p 5432 && echo "✓ 数据库连接正常" || echo "✗ 数据库连接失败"

# 健康检查
echo "4. API 健康检查..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "$HEALTH" | grep -q "healthy" && echo "✓ API 响应正常" || echo "✗ API 响应异常"

echo ""
echo "=== 检查完成 ==="
```

### 3.2 接口测试脚本

```bash
#!/bin/bash
# api_test.sh

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""

# 获取 Token
get_token() {
  TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser001","password":"Test123456"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
}

# 测试任务接口
test_tasks() {
  echo "测试任务接口..."
  curl -s -X GET $BASE_URL/tasks \
    -H "Authorization: Bearer $TOKEN" | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print('✓ 成功' if 'tasks' in d else '✗ 失败')"
}

# 执行测试
get_token
test_tasks
```

---

**文档版本**: v1.0.0  
**最后更新**: 2026-02-25  
**维护者**: AI Agent Development Team

> **提示**: 测试完成后，请及时清理测试数据，特别是测试用户和测试任务。