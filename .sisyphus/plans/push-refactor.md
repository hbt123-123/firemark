# 推送通知框架重构计划

## TL;DR

> **快速摘要**: 将后端推送服务从JPush（极光推送）替换为Web推送（Browser Push）+ Windows桌面通知，保留API框架，更新所有技术文档。

> **交付物**:
> - 新的Web推送服务模块（使用VAPID）
> - Windows桌面通知工具
> - 更新后的技术文档（AGENTS.md, API文档等）

> **预估工作量**: Medium
> **并行执行**: YES - 4个waves
> **关键路径**: 生成VAPID密钥 → 实现Web推送 → 实现Windows通知 → 更新文档

---

## 背景

### 原始需求
用户要求重新构造前后端的推送通知框架：
1. 删除手机端的极光推送模块
2. 仅使用电脑的信息推送（Web推送 + Windows桌面通知）
3. 修改所有技术.md文件

### 访谈总结
**关键讨论**:
- 推送方式: 两者都要（Web推送 + Windows桌面通知）
- 技术文档: 所有.md文件
- 删除范围: 保留框架替换推送方式（保留API结构，只替换底层实现）

**研究发现**:
- **Web推送**: 推荐使用Web Push API + VAPID方案（自托管，无需Firebase）
  - 使用`webpush`库处理加密和订阅管理
  - 需要生成VAPID密钥对
  - 浏览器通过Service Worker接收推送
- **Windows桌面通知**: 推荐使用`windows-toasts`库
  - 支持Win10/11更多特性
  - 注意：需要在桌面客户端环境运行

---

## 工作目标

### 核心目标
将推送服务从JPush（极光推送）迁移到Web推送和Windows桌面通知，同时：
1. 保持API接口兼容性（保留push_token相关端点）
2. 支持两种推送方式并存
3. 更新所有技术文档

### 具体交付物
- [x] 新的Web推送服务模块
- [x] Windows桌面通知工具
- [x] 推送订阅管理API
- [x] 更新后的技术文档

### 完成定义
- [ ] 后端可接收Web推送订阅
- [ ] 后端可发送Web推送通知
- [ ] 后端可发送Windows桌面通知
- [ ] 所有.md文件已更新

### 必须有
- 推送订阅/取消订阅的API端点
- Web推送发送功能
- Windows通知发送功能
- 文档更新

### 必须没有（Guardrails）
- 不能再有JPush相关代码和配置
- 不能破坏现有API兼容性（保留push_token端点）
- 不能删除数据库中已有的push_token数据（迁移）

---

## 验证策略

> **零人工干预** — 所有验证均由agent执行。禁止需要人工手动测试/确认的验收标准。

### 测试决策
- **基础设施存在**: YES
- **自动化测试**: YES (Tests-after)
- **框架**: pytest + pytest-asyncio
- **测试方式**: 任务完成后添加测试

### QA策略
每个任务必须包含agent执行的QA场景（见TODO模板）。
证据保存到 `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Web推送**: 使用curl测试API + 检查订阅存储
- **Windows通知**: 使用Bash调用Python脚本验证通知发送
- **API验证**: 使用curl测试REST端点

---

## 执行策略

### 并行执行Wave

```
Wave 1 (立即启动 — 基础设施):
├── Task 1: 添加webpush依赖到requirements.txt [quick]
├── Task 2: 添加windows-toasts依赖到requirements.txt [quick]
├── Task 3: 创建VAPID密钥生成和管理模块 [quick]
└── Task 4: 创建Web推送订阅模型 [quick]

Wave 2 (Wave 1后 — 核心实现):
├── Task 5: 实现Web推送服务 (send_web_push) [deep]
├── Task 6: 实现Windows通知服务 (send_windows_notification) [deep]
├── Task 7: 重构send_notification_tool支持多推送方式 [unspecified-high]
└── Task 8: 更新push_service使用新推送服务 [unspecified-high]

Wave 3 (Wave 2后 — API适配):
├── Task 9: 添加Web推送订阅API端点 [quick]
├── Task 10: 添加推送方式选择字段到User模型 [quick]
├── Task 11: 更新用户资料API返回推送类型 [quick]
└── Task 12: 更新push-token API支持多类型 [quick]

Wave 4 (Wave 3后 — 文档更新):
├── Task 13: 更新AGENTS.md推送相关描述 [writing]
├── Task 14: 更新API_DOCUMENTATION.md [writing]
├── Task 15: 更新intelligent_tsak开发方案.md [writing]
└── Task 16: 更新其他技术文档 [writing]

Wave FINAL (Wave 4后 — 验证):
├── Task F1: 整体集成测试 [unspecified-high]
└── Task F2: 代码审查 [unspecified-high]
```

### 依赖矩阵
- **1-4**: — — 5-8
- **5-8**: 1-4 — 9-12, F1
- **9-12**: 5-8 — 13-16, F1
- **13-16**: 9-12 — F1
- **F1**: 13-16 — F2
- **F2**: F1 —

### Agent调度摘要
- **Wave 1**: **4** — T1-T4 → `quick`
- **Wave 2**: **4** — T5-T6 → `deep`, T7-T8 → `unspecified-high`
- **Wave 3**: **4** — T9-T12 → `quick`
- **Wave 4**: **4** — T13-T16 → `writing`
- **FINAL**: **2** — F1 → `unspecified-high`, F2 → `unspecified-high`

---

## 待办事项

- [ ] 1. 添加webpush依赖到requirements.txt

  **需要做**:
  - 在requirements.txt添加 `webpush>=1.0.0`
  - 运行 `pip install webpush` 验证

  **不要做**:
  - 不要修改其他无关依赖

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无需特殊技能
  - **技能评估但省略**: N/A

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 1 (与Tasks 2, 3, 4)
  - **阻塞**: Task 5
  - **被阻塞**: 无

  **引用**:
  - `requirements.txt` - 当前依赖文件

  **验收标准**:
  - [ ] `webpush` 包已添加到requirements.txt
  - [ ] `pip install webpush` 成功

  **QA场景**:

  ```
  场景: 验证webpush依赖已添加
    工具: Bash
    步骤:
      1. 运行 pip show webpush
      2. 检查输出包含 "Name: webpush"
    预期结果: 包已安装
    证据: .sisyphus/evidence/task-1-webpush-installed.txt
  ```

  **提交**: YES (Wave 1)
  - 信息: `refactor: 添加webpush依赖`
  - 文件: `requirements.txt`

- [ ] 2. 添加windows-toasts依赖到requirements.txt

  **需要做**:
  - 在requirements.txt添加 `windows-toasts>=0.2.0`
  - 运行 `pip install windows-toasts` 验证

  **不要做**:
  - 不要修改其他无关依赖

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无需特殊技能

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 1 (与Tasks 1, 3, 4)
  - **阻塞**: Task 6
  - **被阻塞**: 无

  **引用**:
  - `requirements.txt` - 当前依赖文件

  **验收标准**:
  - [ ] `windows-toasts` 包已添加到requirements.txt

  **QA场景**:

  ```
  场景: 验证windows-toasts依赖已添加
    工具: Bash
    步骤:
      1. 运行 pip show windows-toasts
    预期结果: 包已安装
    证据: .sisyphus/evidence/task-2-windows-toasts.txt
  ```

  **提交**: YES (Wave 1)
  - 信息: `refactor: 添加windows-toasts依赖`

- [ ] 3. 创建VAPID密钥生成和管理模块

  **需要做**:
  - 创建 `app/services/vapid_manager.py`
  - 实现VAPID密钥对生成
  - 实现密钥存储和加载
  - 添加配置项到settings

  **不要做**:
  - 不要修改现有的JPush配置

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无需特殊技能

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 1
  - **阻塞**: Task 5
  - **被阻塞**: 无

  **引用**:
  - `app/config.py` - 配置管理参考

  **验收标准**:
  - [ ] VAPID密钥生成成功
  - [ ] 密钥可持久化存储
  - [ ] 密钥可被加载使用

  **QA场景**:

  ```
  场景: VAPID密钥生成和存储
    工具: Bash
    步骤:
      1. 运行Python脚本测试密钥生成
      2. 验证生成的公钥和私钥
    预期结果: 密钥生成成功
    证据: .sisyphus/evidence/task-3-vapid-gen.txt
  ```

  **提交**: YES (Wave 1)
  - 信息: `feat: 添加VAPID密钥管理模块`

- [ ] 4. 创建Web推送订阅模型

  **需要做**:
  - 在 `app/models.py` 添加 `PushSubscription` 模型
  - 字段: user_id, endpoint, keys (p256dh, auth), created_at

  **不要做**:
  - 不要修改现有的User模型结构

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无需特殊技能

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 1
  - **阻塞**: Task 5, 9
  - **被阻塞**: 无

  **引用**:
  - `app/models.py` - 模型定义参考

  **验收标准**:
  - [ ] PushSubscription模型创建成功
  - [ ] 可进行基本CRUD操作

  **QA场景**:

  ```
  场景: 验证PushSubscription模型
    工具: Bash
    步骤:
      1. 运行SQLAlchemy检查模型
      2. 验证字段定义正确
    预期结果: 模型定义正确
    证据: .sisyphus/evidence/task-4-model.txt
  ```

  **提交**: YES (Wave 1)
  - 信息: `feat: 添加Web推送订阅模型`

- [ ] 5. 实现Web推送服务 (send_web_push)

  **需要做**:
  - 创建 `app/services/web_push_service.py`
  - 实现加密推送发送
  - 实现订阅管理
  - 处理推送加密（ECDH + AES-GCM）

  **不要做**:
  - 不要调用JPush API

  **推荐Agent配置**:
  - **类别**: `deep`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: Wave 2
  - **阻塞**: Tasks 9, F1
  - **被阻塞**: Tasks 1, 3, 4

  **引用**:
  - `webpush` 库文档
  - `app/services/push_service.py` - 参考结构

  **验收标准**:
  - [ ] 发送Web推送功能实现
  - [ ] 推送加密正确
  - [ ] 可处理过期订阅

  **QA场景**:

  ```
  场景: 发送测试Web推送
    工具: Bash
    步骤:
      1. 创建测试订阅数据
      2. 调用发送函数
      3. 验证无异常
    预期结果: 发送逻辑正确执行
    证据: .sisyphus/evidence/task-5-web-push.txt
  ```

  **提交**: YES (Wave 2)
  - 信息: `feat: 实现Web推送服务`

- [ ] 6. 实现Windows通知服务 (send_windows_notification)

  **需要做**:
  - 创建 `app/services/windows_notification_service.py`
  - 实现Windows Toast通知发送
  - 支持标题、正文、图标等

  **不要做**:
  - 不要在非Windows环境调用

  **推荐Agent配置**:
  - **类别**: `deep`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: Wave 2
  - **阻塞**: Task 8, F1
  - **被阻塞**: Task 2

  **引用**:
  - `windows-toasts` 库文档
  - `app/services/push_service.py` - 参考结构

  **验收标准**:
  - [ ] Windows通知发送功能实现
  - [ ] 通知格式正确

  **QA场景**:

  ```
  场景: 发送测试Windows通知
    工具: Bash
    步骤:
      1. 调用通知服务发送测试通知
    预期结果: 在Windows上显示通知
    证据: .sisyphus/evidence/task-6-windows-notify.txt
  ```

  **提交**: YES (Wave 2)
  - 信息: `feat: 实现Windows通知服务`

- [ ] 7. 重构send_notification_tool支持多推送方式

  **需要做**:
  - 修改 `app/agent/tools/send_notification_tool.py`
  - 添加推送方式参数 (web_push, windows, all)
  - 保留JPush作为fallback但不默认使用

  **不要做**:
  - 不要完全删除JPush代码（保留配置）

  **推荐Agent配置**:
  - **类别**: `unspecified-high`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: Wave 2
  - **阻塞**: Task 8, F1
  - **被阻塞**: Tasks 1, 3, 4

  **引用**:
  - `app/agent/tools/send_notification_tool.py` - 当前实现

  **验收标准**:
  - [ ] 支持指定推送方式
  - [ ] 优先级: Web推送 > Windows通知

  **QA场景**:

  ```
  场景: 测试多推送方式
    工具: Bash
    步骤:
      1. 测试仅Web推送
      2. 测试仅Windows
      3. 测试全部方式
    预期结果: 各种模式正常工作
    证据: .sisyphus/evidence/task-7-multi-push.txt
  ```

  **提交**: YES (Wave 2)
  - 信息: `refactor: 重构通知工具支持多推送方式`

- [ ] 8. 更新push_service使用新推送服务

  **需要做**:
  - 修改 `app/services/push_service.py`
  - 替换JPush调用为Web推送和Windows通知

  **不要做**:
  - 不要删除原有业务逻辑

  **推荐Agent配置**:
  - **类别**: `unspecified-high`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: Wave 2
  - **阻塞**: Task 9
  - **被阻塞**: Tasks 5, 6, 7

  **引用**:
  - `app/services/push_service.py` - 当前实现

  **验收标准**:
  - [ ] 任务提醒使用新推送方式
  - [ ] 日报/复盘使用新推送方式

  **QA场景**:

  ```
  场景: 测试完整推送流程
    工具: Bash
    步骤:
      1. 模拟任务提醒发送
      2. 验证新服务被调用
    预期结果: 新推送服务被正确调用
    证据: .sisyphus/evidence/task-8-push-service.txt
  ```

  **提交**: YES (Wave 2)
  - 信息: `refactor: 更新推送服务使用新实现`

- [ ] 9. 添加Web推送订阅API端点

  **需要做**:
  - 创建 `app/routers/web_push.py`
  - POST /web-push/subscribe - 订阅
  - DELETE /web-push/unsubscribe - 取消订阅
  - GET /web-push/vapid-public-key - 获取公钥

  **不要做**:
  - 不要修改现有API路由

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: Wave 3
  - **阻塞**: Task 13
  - **被阻塞**: Tasks 5, 8

  **引用**:
  - `app/routers/users.py` - 路由风格参考

  **验收标准**:
  - [ ] 订阅API正常工作
  - [ ] 取消订阅API正常工作
  - [ ] 公钥端点返回正确

  **QA场景**:

  ```
  场景: 测试订阅API
    工具: Bash (curl)
    步骤:
      1. POST /api/v1/web-push/subscribe
      2. 验证返回成功
    预期结果: 订阅成功
    证据: .sisyphus/evidence/task-9-subscribe-api.txt
  ```

  **提交**: YES (Wave 3)
  - 信息: `feat: 添加Web推送订阅API`

- [ ] 10. 添加推送方式选择字段到User模型

  **需要做**:
  - 在 `app/models.py` User模型添加 `notification_preference` 字段
  - 字段类型: enum (web_push, windows, all)

  **不要做**:
  - 不要删除现有push_token字段

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 3
  - **阻塞**: Task 11
  - **被阻塞**: Tasks 5, 8

  **验收标准**:
  - [ ] 新字段添加到User模型

  **提交**: YES (Wave 3)
  - 信息: `feat: 添加推送偏好字段`

- [ ] 11. 更新用户资料API返回推送类型

  **需要做**:
  - 修改 `app/routers/users.py`
  - UserResponse添加notification_preference字段

  **不要做**:
  - 不要改变API基本结构

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 3
  - **阻塞**: Task 13
  - **被阻塞**: Tasks 5, 8

  **验收标准**:
  - [ ] API返回推送偏好

  **提交**: YES (Wave 3)
  - 信息: `feat: 更新用户资料API`

- [ ] 12. 更新push-token API支持多类型

  **需要做**:
  - 修改 `app/routers/users.py`
  - PushTokenRequest添加type字段 (web_push, windows, jpush)

  **不要做**:
  - 不要删除现有功能

  **推荐Agent配置**:
  - **类别**: `quick`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 3
  - **阻塞**: Task 13
  - **被阻塞**: Tasks 5, 8

  **验收标准**:
  - [ ] API支持指定推送类型

  **提交**: YES (Wave 3)
  - 信息: `refactor: 更新推送Token API`

- [ ] 13. 更新AGENTS.md推送相关描述

  **需要做**:
  - 在AGENTS.md中更新推送服务描述
  - 说明新的推送架构

  **不要做**:
  - 不要删除其他无关内容

  **推荐Agent配置**:
  - **类别**: `writing`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 4
  - **阻塞**: F1
  - **被阻塞**: Tasks 9, 11, 12

  **引用**:
  - `AGENTS.md` - 当前文档

  **验收标准**:
  - [ ] 推送部分已更新

  **提交**: YES (Wave 4)
  - 信息: `docs: 更新AGENTS.md推送描述`

- [ ] 14. 更新API_DOCUMENTATION.md

  **需要做**:
  - 更新API文档中的推送相关部分
  - 添加新API端点文档

  **不要做**:
  - 不要修改其他API描述

  **推荐Agent配置**:
  - **类别**: `writing`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 4
  - **阻塞**: F1
  - **被阻塞**: Tasks 9, 11, 12

  **引用**:
  - `API_DOCUMENTATION.md` - 当前文档

  **验收标准**:
  - [ ] 推送API文档已更新

  **提交**: YES (Wave 4)
  - 信息: `docs: 更新API文档`

- [ ] 15. 更新intelligent_tsak开发方案.md

  **需要做**:
  - 更新开发方案中的推送架构描述
  - 说明迁移计划

  **不要做**:
  - 不要改变其他技术方案

  **推荐Agent配置**:
  - **类别**: `writing`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 4
  - **阻塞**: F1
  - **被阻塞**: Tasks 9, 11, 12

  **验收标准**:
  - [ ] 开发方案已更新

  **提交**: YES (Wave 4)
  - 信息: `docs: 更新开发方案`

- [ ] 16. 更新其他技术文档

  **需要做**:
  - 检查并更新TESTING.md
  - 检查并更新plan_ai_flutter/README.md

  **不要做**:
  - 不要添加新文档

  **推荐Agent配置**:
  - **类别**: `writing`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: YES
  - **并行组**: Wave 4
  - **阻塞**: F1
  - **被阻塞**: Tasks 9, 11, 12

  **验收标准**:
  - [ ] 相关文档已检查并更新

  **提交**: YES (Wave 4)
  - 信息: `docs: 更新其他技术文档`

- [ ] F1. 整体集成测试

  **需要做**:
  - 完整测试推送流程
  - 验证所有服务集成正常

  **推荐Agent配置**:
  - **类别**: `unspecified-high`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: FINAL
  - **阻塞**: F2
  - **被阻塞**: Tasks 8, 9, 13-16

  **验收标准**:
  - [ ] 端到端测试通过

  **QA场景**:

  ```
  场景: 端到端集成测试
    工具: Bash
    步骤:
      1. 启动服务
      2. 测试完整推送流程
    预期结果: 流程正常
    证据: .sisyphus/evidence/final-integration.txt
  ```

- [ ] F2. 代码审查

  **需要做**:
  - 检查代码质量
  - 确保没有JPush残留

  **推荐Agent配置**:
  - **类别**: `unspecified-high`
  - **技能**: 无

  **并行化**:
  - **可并行运行**: NO
  - **并行组**: FINAL
  - **阻塞**: 无
  - **被阻塞**: F1

  **验收标准**:
  - [ ] 无JPush代码残留
  - [ ] 代码质量符合标准

---

## 最终验证Wave

- [ ] F1. **整体集成测试** — `unspecified-high`
  验证所有推送服务正常工作

- [ ] F2. **代码审查** — `unspecified-high`
  确保无JPush残留，代码质量合格

---

## 提交策略

- **Wave 1**: `refactor: 添加推送依赖和基础模块` — requirements.txt, vapid_manager.py, models.py
- **Wave 2**: `feat: 实现Web推送和Windows通知服务` — web_push_service.py, windows_notification_service.py, send_notification_tool.py, push_service.py
- **Wave 3**: `feat: 添加推送订阅API` — web_push.py, users.py (更新)
- **Wave 4**: `docs: 更新技术文档` — AGENTS.md, API文档, 开发方案

---

## 成功标准

### 验证命令
```bash
pip show webpush  # 应显示已安装
pip show windows-toasts  # 应显示已安装
```

### 最终检查清单
- [ ] 所有JPush配置已移除
- [ ] Web推送服务已实现
- [ ] Windows通知服务已实现
- [ ] 新API端点可正常工作
- [ ] 所有技术文档已更新
- [ ] 代码无JPush残留
