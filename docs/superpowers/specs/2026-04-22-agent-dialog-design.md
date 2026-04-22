# Agent 对话功能设计文档

## 1. 概述

### 1.1 目标
为物流管理系统新增 Agent 对话功能，用户可以通过自然语言与 AI 对话，实现：
- 物流数据查询、筛选、统计
- 订单增删改
- 物流路线优化、成本优化
- 变更 Diff 展示
- 多轮对话上下文保存与恢复

### 1.2 核心特性
- **生成式 + Agent 能力**：不仅回答，还能执行操作
- **写操作需确认**：修改/删除前弹出确认，显示变更内容
- **Diff 展示**：用表格对比变更前后数据
- **历史保存**：多轮对话存入数据库，恢复时重建完整上下文

---

## 2. 数据库设计

### 2.1 表结构变更

**扩展 `chat_history` 表**

```sql
ALTER TABLE chat_history ADD COLUMN session_id VARCHAR(64) NOT NULL DEFAULT '' COMMENT '会话ID，关联同一轮对话';
ALTER TABLE chat_history ADD COLUMN message_order INT NOT NULL DEFAULT 0 COMMENT '消息顺序';
ALTER TABLE chat_history ADD COLUMN action_type VARCHAR(32) DEFAULT NULL COMMENT '动作类型：query/mutation/optimize/code/explain';
ALTER TABLE chat_history ADD COLUMN action_result TEXT DEFAULT NULL COMMENT '执行结果（JSON）';
ALTER TABLE chat_history ADD COLUMN diff_content TEXT DEFAULT NULL COMMENT '变更Diff（JSON）';
```

**新建 `operation_logs` 表（已有，跳过）**

已存在，用于记录所有写操作日志。

### 2.2 消息结构

每条消息包含：
- `session_id`：会话标识，同一轮对话共享
- `message_order`：消息序号
- `user_input`：用户输入
- `ai_response`：AI 响应
- `action_type`：执行的动作类型
- `action_result`：执行结果
- `diff_content`：变更内容（如有）

---

## 3. Agent 架构

### 3.1 组件结构

```
┌─────────────────────────────────────────────────────────┐
│                    Agent 入口 (Agent)                    │
│  接收用户输入 → 意图识别 → 路由分发                       │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┬───────────────┐
           ▼               ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │QueryHandler │ │MutationHandler│ │OptimizeHandler│ │ExplainHandler│
    │  数据查询    │ │  增删改      │ │   优化分析   │ │  纯对话    │
    └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    ┌─────────────┐
                    │  Diff 生成  │
                    │  结果展示    │
                    └─────────────┘
```

### 3.2 Handler 职责

| Handler | 能力 | 示例 | 接口方法 |
|---------|------|------|----------|
| `QueryHandler` | 查询、筛选、统计 | "查一下最近3天的订单" | `handle(intent, context) -> Response` |
| `MutationHandler` | 新增、修改、删除 | "把延误的改成已送达" | `handle(intent, context) -> PlanResponse` |
| `OptimizeHandler` | 路线/成本优化分析 | "优化下物流线路" | `handle(intent, context) -> AnalysisResponse` |
| `ExplainHandler` | 纯对话，无需执行 | "解释一下什么是SLA" | `handle(intent, context) -> Response` |

**Handler 路由协议**：Agent 根据意图识别结果，调用对应 Handler 的标准接口。Handler 返回结构化响应，包含 `type`（query/mutation/optimize/explain）、`content`、`need_confirm`、`diff` 等字段。

### 3.3 意图识别（Intent Detection）

**实现方式**：使用 AI 模型进行零样本分类。

**Prompt 示例**：
```
用户消息：{user_message}

请判断用户想要什么，选择以下意图之一：
- query：需要查询数据库中的物流数据
- mutation：需要对数据库进行增删改操作
- optimize：需要对物流路线/成本进行优化分析
- explain：只是想聊天或了解概念，不需要执行任何操作

只返回一个词：query/mutation/optimize/explain
```

**提取参数**：使用 AI 从用户消息中提取关键参数（时间范围、订单状态、目的地等），构建结构化意图对象。

### 3.4 Agent 执行流程

```
1. 用户输入
   ↓
2. 意图识别（Intent Detection）
   - AI 分类：query/mutation/optimize/explain
   - 提取参数：时间、状态、ID 等
   ↓
3. 路由分发（Routing）
   - 根据意图类型，分发到对应 Handler
   ↓
4a. Query/Optimize/Explain Handler 执行
   → 返回结果给用户
   ↓
4b. Mutation Handler 执行
   → 生成行动计划（Plan）
   → 返回给用户确认（意图确认）
   ↓
5. 用户确认（如需写操作）
   ↓
6. 执行（Mutation 二次确认 Diff）
   ↓
7. 返回结果 + Diff
   ↓
8. 保存到 chat_history
```

### 3.5 安全机制

**写操作分级确认**
1. **意图确认**：告知用户 AI 计划做什么
2. **执行确认**：显示具体变更内容 Diff

**Diff 展示示例**
```
| 订单ID | 原状态 | 新状态 | 操作 |
|--------|--------|--------|------|
| #001   | 延误   | 已送达 | 修改 |
| #002   | 延误   | 已送达 | 修改 |
| #003   | 延误   | 已送达 | 修改 |

确认执行以上 3 条变更？
[确认] [取消]
```

### 3.6 错误处理

| 错误场景 | 处理方式 |
|----------|----------|
| 数据库连接失败 | 返回错误消息："数据库连接失败，请稍后重试" |
| AI 服务超时 | 返回错误消息："AI 服务响应超时，请稍后重试" |
| Session 不存在 | 自动创建新 Session，返回空上下文 |
| 查询结果为空 | 返回："未找到符合条件的记录" |
| Diff 数据过大 | 分页展示，单次最多显示 100 条变更 |
| AI 响应格式错误 | 降级为纯文本响应，记录日志 |
| 写操作无权限 | 返回："您没有执行此操作的权限" |

### 3.7 上下文管理

**上下文构建**：
1. 根据 `session_id` 查询所有历史消息
2. 按 `message_order` 升序排列
3. 构建对话历史列表，每条消息包含 `role`（user/assistant）和 `content`

**上下文长度控制**：
- 保留最近 20 条消息（约 10 轮对话）
- 超出时截断早期消息，保留系统提示词

**系统提示词**：
```
你是一个智能物流助手。用户可以用自然语言查询、修改物流数据。

你的能力：
- 查询订单、筛选统计
- 新增、修改、删除订单
- 分析并优化物流路线和成本

当你需要进行写操作时（增删改），必须先征得用户确认才能执行。
```

---

## 4. 页面设计

### 4.1 新建对话页面

**路由**：`/chat/new` 或 `/chat/<session_id>`

**布局**（类似 ChatGPT，与其他页面保持一致的左上角按钮风格）：
```
┌─────────────────────────────────────────────┐
│ [历史记录]                        智能物流助手│
├─────────────────────────────────────────────┤
│                                             │
│              AI 消息                         │
│                                             │
│              用户消息                        │
│                                             │
│              AI 消息                         │
│                                             │
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ 输入框...                        [发送] │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 4.2 确认弹窗

**意图确认弹窗**
```
┌─────────────────────────────────────────────┐
│           AI 计划执行以下操作               │
├─────────────────────────────────────────────┤
│ 1. 查询最近3天的所有延误订单                 │
│ 2. 将这些订单状态改为"已送达"              │
├─────────────────────────────────────────────┤
│            [确认] [取消]                    │
└─────────────────────────────────────────────┘
```

**Diff 确认弹窗**
```
┌─────────────────────────────────────────────┐
│           即将执行以下变更                  │
├─────────────────────────────────────────────┤
│ 订单ID    原状态    新状态    操作          │
│ #001     延误      已送达    修改           │
│ #002     延误      已送达    修改           │
├─────────────────────────────────────────────┤
│            [确认] [取消]                    │
└─────────────────────────────────────────────┘
```

### 4.3 历史记录页面

在现有历史记录基础上：
- 左侧显示会话列表（按 session_id 分组，取第一条消息作为标题）
- 点击会话恢复对话
- 每个会话显示：标题、创建时间、消息数

---

## 5. API 接口

### 5.1 对话相关

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /api/chat/send` | POST | 发送消息（触发意图识别） |
| `POST /api/chat/confirm` | POST | 确认执行（意图确认 → 执行 Diff 确认） |
| `GET /api/chat/history/<session_id>` | GET | 获取会话历史 |
| `GET /api/chat/sessions` | GET | 获取会话列表 |
| `POST /api/chat/sessions` | POST | 新建会话 |
| `DELETE /api/chat/sessions/<session_id>` | DELETE | 删除会话 |

**两级确认说明**：
- `POST /api/chat/send` 返回 `need_confirm: true` 时，表示需要意图确认
- 用户点击确认后，调用 `POST /api/chat/confirm` 执行操作
- 如果操作涉及数据变更，`confirm` 响应会包含 `diff`，前端再展示 Diff 确认弹窗
- 用户最终确认后，前端再次调用 `POST /api/chat/confirm` 执行真正变更

### 5.2 详细请求/响应规范

**POST /api/chat/sessions**
```json
// POST /api/chat/sessions
// 请求体可选：{"title": "新对话标题"}

// 响应
{
  "success": true,
  "session_id": "sess_xyz789",
  "title": "新对话标题"
}
```

**GET /api/chat/history/<session_id>**
```json
// 响应
{
  "success": true,
  "session_id": "sess_abc123",
  "messages": [
    {
      "message_order": 1,
      "role": "user",
      "content": "最近3天有多少订单",
      "action_type": null,
      "action_result": null,
      "diff_content": null,
      "created_at": "2026-04-22 10:00:00"
    },
    {
      "message_order": 2,
      "role": "assistant",
      "content": "最近3天共有 156 条订单",
      "action_type": "query",
      "action_result": "{\"count\": 156}",
      "diff_content": null,
      "created_at": "2026-04-22 10:00:01"
    }
  ]
}
```

**DELETE /api/chat/sessions/<session_id>**
```json
// 响应
{
  "success": true,
  "message": "会话已删除"
}
```

### 5.3 请求/响应示例

**发送消息**
```json
// POST /api/chat/send
{
  "session_id": "sess_abc123",
  "message": "帮我把最近3天延误的订单改成已送达"
}

// 响应
{
  "success": true,
  "need_confirm": true,
  "action_plan": {
    "steps": [
      "查询最近3天的延误订单",
      "将订单状态修改为已送达"
    ],
    "affected_count": 5
  }
}
```

**确认执行（两阶段）**

阶段一：意图确认
```json
// POST /api/chat/confirm
{
  "session_id": "sess_abc123",
  "action": "mutation",
  "step": "intent",     // 当前阶段：intent 或 diff
  "confirmed": true
}

// 响应（返回 Diff 供二次确认）
{
  "success": true,
  "need_diff_confirm": true,
  "diff": {
    "before": [
      {"id": "001", "status": "延误"},
      {"id": "002", "status": "延误"}
    ],
    "after": [
      {"id": "001", "status": "已送达"},
      {"id": "002", "status": "已送达"}
    ]
  },
  "affected_rows": 2
}
```

阶段二：Diff 确认（前端展示 Diff 表格，用户确认后再次调用）
```json
// POST /api/chat/confirm
{
  "session_id": "sess_abc123",
  "action": "mutation",
  "step": "diff",
  "confirmed": true
}

// 响应（最终执行结果）
{
  "success": true,
  "affected_rows": 2,
  "message": "已成功更新 2 条记录"
}
```

---

## 6. 技术实现

### 6.1 目录结构

```
internal/
├── service/
│   └── chat_agent/
│       ├── __init__.py
│       ├── http.py          # HTTP 路由
│       ├── service.py       # 核心逻辑
│       ├── agent.py         # Agent 引擎（意图识别 + 路由）
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── base.py      # Handler 基类，定义标准接口
│       │   ├── query.py     # 查询 Handler
│       │   ├── mutation.py  # 增删改 Handler
│       │   ├── optimize.py  # 优化 Handler
│       │   └── explain.py   # 纯对话 Handler
│       └── intent.py        # 意图识别（备用：规则匹配）
```

**Handler 基类接口**（`base.py`）：
```python
class BaseHandler:
    def __init__(self, dao: ShipmentDAO, model: AIModelHandler):
        self.dao = dao
        self.model = model

    async def handle(self, intent: dict, context: list) -> Response:
        """处理请求，返回结构化响应"""
        raise NotImplementedError
```

**Response 结构**：
```python
@dataclass
class HandlerResponse:
    type: str           # query/mutation/optimize/explain
    content: str        # 显示给用户的文本
    need_confirm: bool  # 是否需要用户确认
    action_plan: dict   # 行动计划（mutation 时）
    diff: dict          # 变更 Diff（执行后）
```

### 6.2 Session 管理

- `session_id` 生成：用 UUID 或时间戳+随机数
- 第一条消息时创建 session
- 页面离开时 session 仍保留在数据库

### 6.3 上下文恢复

恢复对话时：
1. 根据 `session_id` 查询所有消息
2. 按 `message_order` 排序
3. 构建对话上下文传给 AI

### 6.4 AI/LLM 集成

**使用的模型**：与现有 `AIModelHandler` 相同（`MiniMax-M2.7-highspeed`）

**调用方式**：
- 意图识别：短 prompt，直接调用 `generate_response()`
- 对话生成：带上下文的 `generate_response_stream()`
- 代码执行：复用的 `CodeGenService.execute_code()`

**模型限制**：
- 意图识别使用较短 prompt，避免上下文干扰
- 对话上下文保留最近 20 条消息，防止超出 token 限制

---

## 7. 测试场景

| 场景 | 输入 | 预期结果 |
|------|------|----------|
| 查询统计 | "最近3天有多少订单" | 返回统计结果 |
| 修改确认 | "把延误的改成已送达" | 弹出确认，显示 Diff |
| 优化分析 | "帮我优化下物流线路" | 返回优化建议 |
| 纯对话 | "什么是SLA" | 直接回答，不触发操作 |
| 历史恢复 | 点击历史会话 | 加载完整上下文 |
