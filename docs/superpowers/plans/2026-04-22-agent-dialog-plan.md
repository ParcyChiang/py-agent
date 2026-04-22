# Agent 对话功能实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 Agent 对话功能，支持自然语言查询/修改物流数据、多轮上下文、历史保存

**Architecture:**
- 后端：Flask + 异步 Agent 引擎，Handler 模式（Query/Mutation/Optimize/Explain）
- 前端：类 ChatGPT 单页对话界面，SSE 流式响应
- 数据库：扩展 chat_history 表，新增 session_id/message_order/action_type 等字段

**Tech Stack:** Python/Flask, SSE, MySQL, HTML/Jinja2

---

## 文件结构

```
internal/
├── pkg/
│   └── dao.py                    # 修改：ChatHistoryDAO 新增 session 方法
├── service/
│   ├── service.py                # 修改：注册 ChatAgentHttp
│   └── chat_agent/               # 新建
│       ├── __init__.py
│       ├── http.py               # 新建：HTTP 路由
│       ├── service.py            # 新建：Session/消息管理
│       ├── agent.py              # 新建：Agent 引擎 + 意图识别
│       └── handlers/
│           ├── __init__.py
│           ├── base.py           # 新建：Handler 基类
│           ├── query.py          # 新建：查询 Handler
│           ├── mutation.py       # 新建：增删改 Handler
│           ├── optimize.py       # 新建：优化 Handler
│           └── explain.py        # 新建：纯对话 Handler
templates/
└── chat.html                     # 新建：对话页面
```

---

## Chunk 1: 数据库层

### Task 1: 扩展 ChatHistoryDAO

**Files:**
- Modify: `internal/pkg/dao.py`

- [ ] **Step 1: 添加 session 相关查询方法**

在 `ChatHistoryDAO` 类中添加以下方法：

```python
def create_session(self, user_id: int, username: str, title: str = "") -> str:
    """创建新会话，返回 session_id"""
    import uuid
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO chat_history
                   (user_id, username, page, title, user_input, ai_response, session_id, message_order)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, username, 'chat_agent', title, '__SESSION_START__', '', session_id, 0)
            )
            conn.commit()
            return session_id

def add_message(self, user_id: int, username: str, session_id: str,
                message_order: int, role: str, content: str,
                action_type: str = None, action_result: str = None,
                diff_content: str = None) -> None:
    """添加消息"""
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO chat_history
                   (user_id, username, page, title, user_input, ai_response,
                    session_id, message_order, action_type, action_result, diff_content)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, username, 'chat_agent', '', content if role == 'user' else '',
                 content if role == 'assistant' else '',
                 session_id, message_order, action_type, action_result, diff_content)
            )
            conn.commit()

def get_session_messages(self, session_id: str) -> List[Dict]:
    """获取会话所有消息，按 message_order 排序"""
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT id, user_input, ai_response, session_id, message_order,
                          action_type, action_result, diff_content, created_at
                   FROM chat_history
                   WHERE session_id = %s AND user_input != '__SESSION_START__'
                   ORDER BY message_order ASC""",
                (session_id,)
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'role': 'user' if row['user_input'] else 'assistant',
                    'content': row['user_input'] or row['ai_response'],
                    'message_order': row['message_order'],
                    'action_type': row['action_type'],
                    'action_result': row['action_result'],
                    'diff_content': row['diff_content'],
                    'created_at': row['created_at']
                })
            return result

def get_user_sessions(self, user_id: int, limit: int = 50) -> List[Dict]:
    """获取用户会话列表（按 session_id 分组）"""
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT session_id,
                          MAX(CASE WHEN user_input != '__SESSION_START__'
                              THEN COALESCE(user_input, ai_response) ELSE NULL END) as title,
                          COUNT(*) as message_count,
                          MAX(created_at) as last_updated
                   FROM chat_history
                   WHERE user_id = %s AND page = 'chat_agent'
                   GROUP BY session_id
                   ORDER BY last_updated DESC
                   LIMIT %s""",
                (user_id, limit)
            )
            return cursor.fetchall()

def delete_session(self, session_id: str, user_id: int) -> bool:
    """删除会话"""
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM chat_history WHERE session_id = %s AND user_id = %s",
                (session_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
```

- [ ] **Step 2: 添加 shipment 批量更新方法**

在 `ShipmentDAO` 类末尾添加：

```python
def batch_update_status(self, shipment_ids: List[str], new_status: str) -> Tuple[int, List[Dict], List[Dict]]:
    """批量更新状态，返回 (成功数, 变更前, 变更后)"""
    before_states = []
    after_states = []
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # 获取变更前的状态
                placeholders = ','.join(['%s'] * len(shipment_ids))
                cursor.execute(f"SELECT id, status FROM shipments WHERE id IN ({placeholders})", shipment_ids)
                for row in cursor.fetchall():
                    before_states.append({'id': row['id'], 'status': row['status']})

                # 执行更新
                cursor.execute(
                    f"UPDATE shipments SET status = %s WHERE id IN ({placeholders})",
                    [new_status] + shipment_ids
                )
                conn.commit()

                # 获取变更后的状态
                cursor.execute(f"SELECT id, status FROM shipments WHERE id IN ({placeholders})", shipment_ids)
                for row in cursor.fetchall():
                    after_states.append({'id': row['id'], 'status': row['status']})

                return cursor.rowcount, before_states, after_states
            except Exception as e:
                conn.rollback()
                raise
```

- [ ] **Step 3: 添加 shipment 按条件查询方法**

```python
def get_shipments_by_criteria(self, status: str = None, days: int = None,
                               origin: str = None, destination: str = None,
                               limit: int = 1000) -> List[Dict]:
    """按条件查询物流记录"""
    conditions = []
    params = []
    if status:
        conditions.append("status = %s")
        params.append(status)
    if days:
        conditions.append(f"created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)")
        params.append(days)
    if origin:
        conditions.append("origin LIKE %s")
        params.append(f"%{origin}%")
    if destination:
        conditions.append("destination LIKE %s")
        params.append(f"%{destination}%")

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    with self.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM shipments WHERE {where_clause} ORDER BY created_at DESC LIMIT %s",
                params + [limit]
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                row['dimensions'] = json.loads(row.get('dimensions') or '{}')
                result.append(row)
            return result
```

- [ ] **Step 4: Commit**

```bash
git add internal/pkg/dao.py
git commit -m "feat: 扩展 ChatHistoryDAO 支持 session，新增 shipment 批量更新和条件查询"
```

---

## Chunk 2: Agent 核心

### Task 2: Handler 基类

**Files:**
- Create: `internal/service/chat_agent/__init__.py`
- Create: `internal/service/chat_agent/handlers/__init__.py`
- Create: `internal/service/chat_agent/handlers/base.py`

- [ ] **Step 1: 创建 __init__.py 文件**

```bash
# 创建空 __init__.py 文件
touch internal/service/chat_agent/__init__.py
touch internal/service/chat_agent/handlers/__init__.py
```

- [ ] **Step 2: 创建 base.py**

```python
# internal/service/chat_agent/handlers/base.py
"""Handler 基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json


@dataclass
class HandlerResponse:
    """Handler 返回结构"""
    type: str                    # query/mutation/optimize/explain
    content: str                 # 显示给用户的文本
    need_confirm: bool = False   # 是否需要用户确认
    action_plan: Dict = field(default_factory=dict)  # 行动计划
    diff: Dict = field(default_factory=dict)        # 变更 Diff
    error: str = None           # 错误信息


class BaseHandler(ABC):
    """Handler 基类"""

    def __init__(self, dao, model):
        self.dao = dao
        self.model = model

    @abstractmethod
    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理请求"""
        raise NotImplementedError

    def parse_result(self, result_text: str, key: str, default=None):
        """简单解析 JSON 结果"""
        try:
            data = json.loads(result_text)
            return data.get(key, default)
        except:
            return default
```

- [ ] **Step 3: Commit**

```bash
git add internal/service/chat_agent/__init__.py internal/service/chat_agent/handlers/__init__.py internal/service/chat_agent/handlers/base.py
git commit -m "feat: 添加 Handler 基类 HandlerResponse"
```

### Task 3: QueryHandler

**Files:**
- Create: `internal/service/chat_agent/handlers/query.py`

- [ ] **Step 1: 创建 query.py**

```python
# internal/service/chat_agent/handlers/query.py
"""查询 Handler"""
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class QueryHandler(BaseHandler):
    """查询 Handler - 处理数据查询请求"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理查询请求"""
        params = intent.get('params', {})
        status = params.get('status')
        days = params.get('days')
        origin = params.get('origin')
        destination = params.get('destination')

        try:
            shipments = self.dao.get_shipments_by_criteria(
                status=status,
                days=days,
                origin=origin,
                destination=destination
            )

            if not shipments:
                return HandlerResponse(
                    type='query',
                    content='未找到符合条件的物流记录',
                    need_confirm=False
                )

            # 生成统计摘要
            total = len(shipments)
            status_dist = {}
            for s in shipments:
                st = s.get('status', 'unknown')
                status_dist[st] = status_dist.get(st, 0) + 1

            summary = f"共找到 {total} 条物流记录：\n"
            for st, cnt in status_dist.items():
                summary += f"- {st}: {cnt} 条\n"

            # 如果记录不多，显示详细信息
            if total <= 20:
                summary += "\n详细信息：\n"
                for s in shipments[:20]:
                    summary += f"[{s['id']}] {s['origin']} → {s['destination']} | 状态: {s['status']}\n"

            return HandlerResponse(
                type='query',
                content=summary,
                need_confirm=False,
                action_result=json.dumps({'count': total, 'status_distribution': status_dist})
            )
        except Exception as e:
            return HandlerResponse(
                type='query',
                content=f'查询失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )
```

- [ ] **Step 2: Commit**

```bash
git add internal/service/chat_agent/handlers/query.py
git commit -m "feat: 添加 QueryHandler"
```

### Task 4: MutationHandler

**Files:**
- Create: `internal/service/chat_agent/handlers/mutation.py`

- [ ] **Step 1: 创建 mutation.py**

```python
# internal/service/chat_agent/handlers/mutation.py
"""增删改 Handler"""
import json
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class MutationHandler(BaseHandler):
    """Mutation Handler - 处理数据增删改请求"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理写操作请求"""
        params = intent.get('params', {})
        action = params.get('action')  # update/delete/insert
        filters = params.get('filters', {})
        updates = params.get('updates', {})

        try:
            if action == 'update':
                return await self._handle_update(intent, filters, updates)
            elif action == 'delete':
                return await self._handle_delete(intent, filters)
            else:
                return HandlerResponse(
                    type='mutation',
                    content=f'不支持的操作类型: {action}',
                    need_confirm=False,
                    error=f'Unknown action: {action}'
                )
        except Exception as e:
            return HandlerResponse(
                type='mutation',
                content=f'操作失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    async def _handle_update(self, intent: Dict, filters: Dict, updates: Dict) -> HandlerResponse:
        """处理更新操作 - 返回行动计划，等待确认"""
        # 构造 SQL 条件
        conditions = []
        params = []
        if 'status' in filters:
            conditions.append("status = %s")
            params.append(filters['status'])
        if 'days' in filters:
            conditions.append(f"created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)")
            params.append(filters['days'])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self.dao.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT id, status FROM shipments WHERE {where_clause} LIMIT 100",
                    params
                )
                affected = cursor.fetchall()

        if not affected:
            return HandlerResponse(
                type='mutation',
                content='未找到需要更新的记录',
                need_confirm=False
            )

        affected_ids = [r['id'] for r in affected]
        affected_count = len(affected_ids)

        # 构造行动计划
        new_status = updates.get('status', '')
        plan = {
            'action': 'update',
            'filters': filters,
            'updates': updates,
            'affected_ids': affected_ids,
            'affected_count': affected_count,
            'description': f"将 {affected_count} 条记录的状态更新为 '{new_status}'"
        }

        plan_text = f"我计划执行以下操作：\n"
        plan_text += f"1. 根据条件筛选出 {affected_count} 条物流记录\n"
        plan_text += f"2. 将它们的状态更新为 '{new_status}'\n"
        plan_text += f"\n是否确认执行？"

        return HandlerResponse(
            type='mutation',
            content=plan_text,
            need_confirm=True,
            action_plan=plan
        )

    async def _handle_delete(self, intent: Dict, filters: Dict) -> HandlerResponse:
        """处理删除操作"""
        return HandlerResponse(
            type='mutation',
            content='删除操作暂未实现',
            need_confirm=False,
            error='Delete not implemented'
        )

    async def execute_update(self, plan: Dict) -> HandlerResponse:
        """执行更新 - Diff 确认后调用"""
        try:
            affected_ids = plan.get('affected_ids', [])
            new_status = plan.get('updates', {}).get('status')

            if not affected_ids or not new_status:
                return HandlerResponse(
                    type='mutation',
                    content='参数错误',
                    need_confirm=False,
                    error='Missing parameters'
                )

            count, before, after = self.dao.batch_update_status(affected_ids, new_status)

            return HandlerResponse(
                type='mutation',
                content=f'成功更新 {count} 条记录',
                need_confirm=False,
                diff={'before': before, 'after': after},
                action_result=json.dumps({'affected_rows': count})
            )
        except Exception as e:
            return HandlerResponse(
                type='mutation',
                content=f'更新失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )
```

- [ ] **Step 2: Commit**

```bash
git add internal/service/chat_agent/handlers/mutation.py
git commit -m "feat: 添加 MutationHandler"
```

### Task 5: OptimizeHandler

**Files:**
- Create: `internal/service/chat_agent/handlers/optimize.py`

- [ ] **Step 1: 创建 optimize.py**

```python
# internal/service/chat_agent/handlers/optimize.py
"""优化 Handler"""
import json
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class OptimizeHandler(BaseHandler):
    """Optimize Handler - 处理物流优化请求"""

    SYSTEM_PROMPT = """你是一个物流优化专家。请分析物流数据，提出优化建议。

分析维度：
1. 路线优化：根据发货地/收货地分布，推荐更高效的集散中心布局
2. 成本优化：分析各路线的运费、重量分布，推荐更经济的快递公司组合
3. 时效优化：分析延误原因，提出改进措施

请用结构化的方式输出优化建议。"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理优化请求"""
        params = intent.get('params', {})
        optimize_type = params.get('type', 'route')  # route/cost/time

        try:
            # 获取全量数据用于分析
            shipments, _ = self.dao.get_all_shipments(limit=5000)

            if not shipments:
                return HandlerResponse(
                    type='optimize',
                    content='没有足够的物流数据进行分析',
                    need_confirm=False
                )

            # 构建分析上下文
            analysis_context = self._build_analysis_context(shipments, optimize_type)

            # 调用 AI 生成优化建议
            prompt = f"优化类型：{optimize_type}\n\n数据概览：\n{analysis_context}"
            suggestions = await self._generate_suggestions(prompt)

            return HandlerResponse(
                type='optimize',
                content=suggestions,
                need_confirm=False,
                action_result=json.dumps({'optimize_type': optimize_type, 'data_count': len(shipments)})
            )
        except Exception as e:
            return HandlerResponse(
                type='optimize',
                content=f'优化分析失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    def _build_analysis_context(self, shipments: List[Dict], optimize_type: str) -> str:
        """构建分析上下文"""
        if optimize_type == 'route':
            routes = {}
            for s in shipments:
                key = (s.get('origin_city', ''), s.get('destination_city', ''))
                routes[key] = routes.get(key, 0) + 1
            top_routes = sorted(routes.items(), key=lambda x: x[1], reverse=True)[:10]
            context = "热门路线统计：\n"
            for (o, d), cnt in top_routes:
                context += f"- {o} → {d}: {cnt} 单\n"
            return context

        elif optimize_type == 'cost':
            companies = {}
            for s in shipments:
                c = s.get('courier_company', 'unknown')
                fee = float(s.get('shipping_fee', 0) or 0)
                if c not in companies:
                    companies[c] = {'count': 0, 'total_fee': 0}
                companies[c]['count'] += 1
                companies[c]['total_fee'] += fee

            context = "各快递公司费用统计：\n"
            for c, data in sorted(companies.items(), key=lambda x: x[1]['total_fee']/max(x[1]['count'],1)):
                avg = data['total_fee'] / max(data['count'], 1)
                context += f"- {c}: {data['count']} 单, 平均运费 {avg:.2f} 元\n"
            return context

        else:
            return f"共有 {len(shipments)} 条物流记录"

    async def _generate_suggestions(self, prompt: str) -> str:
        """调用 AI 生成优化建议"""
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"
        response = await self.model.generate_response_stream(full_prompt, "")

        suggestions = ""
        async for chunk in response:
            if chunk['type'] == 'text':
                suggestions += chunk['content']

        return suggestions if suggestions else "分析完成，未生成具体建议"
```

- [ ] **Step 2: Commit**

```bash
git add internal/service/chat_agent/handlers/optimize.py
git commit -m "feat: 添加 OptimizeHandler"
```

### Task 6: ExplainHandler

**Files:**
- Create: `internal/service/chat_agent/handlers/explain.py`

- [ ] **Step 1: 创建 explain.py**

```python
# internal/service/chat_agent/handlers/explain.py
"""纯对话 Handler"""
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class ExplainHandler(BaseHandler):
    """Explain Handler - 处理无需执行操作的对话"""

    SYSTEM_PROMPT = """你是一个智能物流助手。用户只是想了解概念或闲聊，不需要执行任何数据库操作。

请用友好、专业的方式回答用户的问题。"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理对话请求"""
        user_message = intent.get('message', '')

        try:
            # 构建对话上下文
            history = self._build_messages(context, user_message)
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{history}"

            # 调用 AI 生成回复
            response_text = ""
            async for chunk in self.model.generate_response_stream(full_prompt, ""):
                if chunk['type'] == 'text':
                    response_text += chunk['content']

            return HandlerResponse(
                type='explain',
                content=response_text or '抱歉，我无法生成回复',
                need_confirm=False
            )
        except Exception as e:
            return HandlerResponse(
                type='explain',
                content=f'抱歉，处理您的请求时出现错误: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    def _build_messages(self, context: List[Dict], current_message: str) -> str:
        """构建对话历史上下文"""
        history = ""
        for msg in context[-10:]:  # 最近 10 条消息
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'user':
                history += f"用户：{content}\n"
            else:
                history += f"助手：{content}\n"
        history += f"用户：{current_message}\n"
        return history
```

- [ ] **Step 2: Commit**

```bash
git add internal/service/chat_agent/handlers/explain.py
git commit -m "feat: 添加 ExplainHandler"
```

### Task 7: Intent Detection & Agent Router

**Files:**
- Create: `internal/service/chat_agent/agent.py`

- [ ] **Step 1: 创建 agent.py**

```python
# internal/service/chat_agent/agent.py
"""Agent 引擎 - 意图识别 + 路由分发"""
import json
import re
from typing import Dict, List, Optional

from .handlers.base import HandlerResponse
from .handlers.query import QueryHandler
from .handlers.mutation import MutationHandler
from .handlers.optimize import OptimizeHandler
from .handlers.explain import ExplainHandler


class Agent:
    """Agent 引擎"""

    INTENT_PROMPT = """用户消息：{message}

请判断用户想要什么，选择以下意图之一：
- query：需要查询数据库中的物流数据（统计、筛选等）
- mutation：需要对数据库进行增删改操作
- optimize：需要对物流路线/成本进行分析优化
- explain：只是想聊天或了解概念，不需要执行任何操作

只返回一个词：query/mutation/optimize/explain"""

    PARAM_EXTRACT_PROMPT = """用户消息：{message}

请从消息中提取关键参数，JSON格式：
- status: 物流状态（如延误、已送达、运输中）
- days: 最近天数（如3天、7天）
- origin: 发货地关键词
- destination: 收货地关键词
- action: 操作类型（update/delete/insert）
- updates: 要更新的字段和值（如 status: 已送达）
- optimize_type: 优化类型（route/cost/time）

只返回 JSON，不要有其他内容。如果参数不存在则不包含该字段。"""

    def __init__(self, dao, model):
        self.dao = dao
        self.model = model
        self.handlers = {
            'query': QueryHandler(dao, model),
            'mutation': MutationHandler(dao, model),
            'optimize': OptimizeHandler(dao, model),
            'explain': ExplainHandler(dao, model),
        }

    async def process(self, message: str, context: List[Dict]) -> HandlerResponse:
        """处理用户消息"""
        # 1. 意图识别
        intent_type = await self._detect_intent(message)
        intent_type = intent_type.strip().lower()

        if intent_type not in ('query', 'mutation', 'optimize', 'explain'):
            intent_type = 'explain'  # 默认走对话

        # 2. 参数提取
        params = await self._extract_params(message)

        # 3. 构建意图对象
        intent = {
            'type': intent_type,
            'message': message,
            'params': params
        }

        # 4. 路由到 Handler
        handler = self.handlers.get(intent_type)
        if not handler:
            return HandlerResponse(
                type='explain',
                content='抱歉，无法处理您的请求',
                need_confirm=False,
                error='No handler found'
            )

        # 5. 执行处理
        response = await handler.handle(intent, context)

        return response

    async def execute_mutation(self, plan: Dict) -> HandlerResponse:
        """执行已确认的 mutation"""
        handler = self.handlers['mutation']
        if hasattr(handler, 'execute_update'):
            return await handler.execute_update(plan)
        return HandlerResponse(
            type='mutation',
            content='Handler 不支持执行',
            need_confirm=False,
            error='execute_update not available'
        )

    async def _detect_intent(self, message: str) -> str:
        """识别用户意图"""
        prompt = self.INTENT_PROMPT.format(message=message)
        try:
            response = await self.model.generate_response_stream(prompt, "")
            result = ""
            async for chunk in response:
                if chunk['type'] == 'text':
                    result += chunk['content']
            return result.strip()
        except Exception as e:
            return 'explain'  # 出错默认走对话

    async def _extract_params(self, message: str) -> Dict:
        """提取参数"""
        prompt = self.PARAM_EXTRACT_PROMPT.format(message=message)
        try:
            response = await self.model.generate_response_stream(prompt, "")
            result = ""
            async for chunk in response:
                if chunk['type'] == 'text':
                    result += chunk['content']
            # 尝试解析 JSON
            # 清理可能的 markdown 代码块
            result = re.sub(r'```json\s*', '', result)
            result = re.sub(r'```\s*', '', result)
            result = result.strip()
            return json.loads(result)
        except Exception as e:
            return {}  # 解析失败返回空参数
```

- [ ] **Step 2: Commit**

```bash
git add internal/service/chat_agent/agent.py
git commit -m "feat: 添加 Agent 引擎（意图识别 + 路由）"
```

---

## Chunk 3: Service 层

### Task 8: ChatAgentService

**Files:**
- Create: `internal/service/chat_agent/service.py`

- [ ] **Step 1: 创建 service.py**

```python
# internal/service/chat_agent/service.py
"""ChatAgent Service - Session 和消息管理"""
import json
import uuid
from typing import Dict, List, Optional, Tuple

from internal.pkg.dao import ChatHistoryDAO, ShipmentDAO
from internal.pkg.models.model_handler import AIModelHandler
from .agent import Agent


class ChatAgentService:
    """ChatAgent 服务"""

    MAX_CONTEXT_MESSAGES = 20  # 最多保留 20 条消息

    def __init__(self):
        self.chat_dao = ChatHistoryDAO()
        self.shipment_dao = ShipmentDAO()
        self.model = AIModelHandler()
        self.agent = Agent(self.shipment_dao, self.model)

    def create_session(self, user_id: int, username: str, title: str = "") -> str:
        """创建新会话"""
        if not title:
            title = f"新对话"
        return self.chat_dao.create_session(user_id, username, title)

    def get_sessions(self, user_id: int) -> List[Dict]:
        """获取用户的会话列表"""
        return self.chat_dao.get_user_sessions(user_id)

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """获取会话的所有消息"""
        messages = self.chat_dao.get_session_messages(session_id)
        # 限制上下文长度
        if len(messages) > self.MAX_CONTEXT_MESSAGES:
            messages = messages[-self.MAX_CONTEXT_MESSAGES:]
        return messages

    def delete_session(self, session_id: str, user_id: int) -> bool:
        """删除会话"""
        return self.chat_dao.delete_session(session_id, user_id)

    async def send_message(self, user_id: int, username: str,
                          session_id: str, message: str) -> Tuple[Dict, int]:
        """发送消息并处理"""
        # 获取上下文
        context = self.get_session_messages(session_id)

        # 处理消息
        response = await self.agent.process(message, context)

        # 保存用户消息
        user_msg_order = len(context) * 2 + 1
        self.chat_dao.add_message(
            user_id, username, session_id,
            user_msg_order, 'user', message
        )

        # 保存 AI 响应
        ai_msg_order = user_msg_order + 1
        self.chat_dao.add_message(
            user_id, username, session_id,
            ai_msg_order, 'assistant', response.content,
            action_type=response.type,
            action_result=response.action_result,
            diff_content=json.dumps(response.diff) if response.diff else None
        )

        return {
            'type': response.type,
            'content': response.content,
            'need_confirm': response.need_confirm,
            'action_plan': response.action_plan,
            'diff': response.diff,
            'error': response.error
        }, ai_msg_order

    async def confirm_action(self, user_id: int, username: str,
                            session_id: str, step: str, plan: Dict) -> Dict:
        """确认执行操作"""
        if step == 'intent':
            # 意图确认 → 返回 Diff
            result = await self.agent.execute_mutation(plan)
            # 更新最后一条 AI 消息的 diff
            return {
                'success': True,
                'need_diff_confirm': True,
                'diff': result.diff,
                'affected_rows': len(plan.get('affected_ids', [])),
                'content': result.content
            }
        elif step == 'diff':
            # Diff 确认 → 执行真正更新
            result = await self.agent.execute_mutation(plan)
            return {
                'success': True,
                'affected_rows': len(plan.get('affected_ids', [])),
                'message': result.content
            }
        else:
            return {
                'success': False,
                'message': f'未知的确认步骤: {step}'
            }
```

- [ ] **Step 2: Commit**

```bash
git add internal/service/chat_agent/service.py
git commit -m "feat: 添加 ChatAgentService"
```

---

## Chunk 4: HTTP 层

### Task 9: ChatAgentHttp

**Files:**
- Create: `internal/service/chat_agent/http.py`
- Modify: `internal/service/service.py`

- [ ] **Step 1: 创建 http.py**

```python
# internal/service/chat_agent/http.py
"""ChatAgent HTTP 处理器"""
import asyncio
import json
import logging
from flask import request, render_template, Response, session

from .service import ChatAgentService
from internal.pkg.response import success, error
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class ChatAgentHttp:
    """ChatAgent HTTP 处理器"""

    def __init__(self):
        self.service = ChatAgentService()

    def routes(self, app):
        """注册 ChatAgent 路由"""
        # 页面路由
        app.add_url_rule('/page/chat_agent', endpoint='page_chat_agent',
                         view_func=login_required(self.page_chat_agent))
        app.add_url_rule('/page/chat', endpoint='page_chat',
                         view_func=login_required(self.page_chat))
        app.add_url_rule('/page/chat/<session_id>', endpoint='page_chat_session',
                         view_func=login_required(self.page_chat_session))

        # API 路由
        app.add_url_rule('/api/chat/sessions', endpoint='chat_sessions_list',
                         view_func=login_required(self.list_sessions), methods=['GET'])
        app.add_url_rule('/api/chat/sessions', endpoint='chat_sessions_create',
                         view_func=login_required(self.create_session), methods=['POST'])
        app.add_url_rule('/api/chat/sessions/<session_id>', endpoint='chat_sessions_delete',
                         view_func=login_required(self.delete_session), methods=['DELETE'])
        app.add_url_rule('/api/chat/history/<session_id>', endpoint='chat_history',
                         view_func=login_required(self.get_history), methods=['GET'])
        app.add_url_rule('/api/chat/send', endpoint='chat_send',
                         view_func=login_required(self.send_message), methods=['POST'])
        app.add_url_rule('/api/chat/confirm', endpoint='chat_confirm',
                         view_func=login_required(self.confirm_action), methods=['POST'])

    def page_chat_agent(self):
        """ChatAgent 页面"""
        return render_template('chat.html')

    def page_chat(self):
        """新建对话页面"""
        return render_template('chat.html')

    def page_chat_session(self, session_id: str):
        """会话页面"""
        return render_template('chat.html', session_id=session_id)

    def list_sessions(self):
        """获取会话列表"""
        user_id = session.get('user_id')
        try:
            sessions = self.service.get_sessions(user_id)
            return success(data={'sessions': sessions})
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return error(f"获取失败: {str(e)}")

    def create_session(self):
        """创建会话"""
        user_id = session.get('user_id')
        username = session.get('username', '')
        data = request.get_json() or {}
        title = data.get('title', '')

        try:
            session_id = self.service.create_session(user_id, username, title)
            return success(data={'session_id': session_id, 'title': title or '新对话'})
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return error(f"创建失败: {str(e)}")

    def delete_session(self, session_id: str):
        """删除会话"""
        user_id = session.get('user_id')
        try:
            if self.service.delete_session(session_id, user_id):
                return success(message='会话已删除')
            return error('删除失败，会话不存在或无权删除')
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return error(f"删除失败: {str(e)}")

    def get_history(self, session_id: str):
        """获取会话历史"""
        user_id = session.get('user_id')
        try:
            messages = self.service.get_session_messages(session_id)
            return success(data={'session_id': session_id, 'messages': messages})
        except Exception as e:
            logger.error(f"获取会话历史失败: {e}")
            return error(f"获取失败: {str(e)}")

    def send_message(self):
        """发送消息"""
        user_id = session.get('user_id')
        username = session.get('username', '')
        data = request.get_json()

        session_id = data.get('session_id')
        message = data.get('message', '').strip()

        if not session_id:
            return error('session_id 不能为空')
        if not message:
            return error('消息不能为空')

        try:
            result, msg_order = asyncio.run(
                self.service.send_message(user_id, username, session_id, message)
            )
            return success(data=result)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return error(f"处理失败: {str(e)}")

    def confirm_action(self):
        """确认操作"""
        user_id = session.get('user_id')
        username = session.get('username', '')
        data = request.get_json()

        session_id = data.get('session_id')
        step = data.get('step')  # 'intent' or 'diff'
        confirmed = data.get('confirmed', False)

        if not confirmed:
            return success(message='操作已取消')

        if not session_id or not step:
            return error('参数不完整')

        try:
            # 从上下文中获取 plan
            messages = self.service.get_session_messages(session_id)
            plan = self._extract_plan_from_messages(messages)

            if not plan:
                return error('无法找到待执行的操作')

            result = asyncio.run(
                self.service.confirm_action(user_id, username, session_id, step, plan)
            )
            return success(data=result)
        except Exception as e:
            logger.error(f"确认操作失败: {e}")
            return error(f"操作失败: {str(e)}")

    def _extract_plan_from_messages(self, messages: List[Dict]) -> Optional[Dict]:
        """从消息中提取最后一个 action_plan"""
        for msg in reversed(messages):
            if msg.get('role') == 'assistant' and msg.get('action_type') == 'mutation':
                try:
                    action_result = msg.get('action_result')
                    if action_result:
                        return json.loads(action_result)
                except:
                    pass
        return None
```

- [ ] **Step 2: 修改 service.py 注册路由**

```python
# 在 service.py 中添加
from internal.service.chat_agent.http import ChatAgentHttp

# 在 register_routes 函数中
chat_agent_http = ChatAgentHttp()
chat_agent_http.routes(app)
```

- [ ] **Step 3: Commit**

```bash
git add internal/service/chat_agent/http.py internal/service/service.py
git commit -m "feat: 添加 ChatAgentHttp 并注册路由"
```

---

## Chunk 5: 前端页面

### Task 10: Chat HTML 模板

**Files:**
- Create: `templates/chat.html`

- [ ] **Step 1: 创建 chat.html**

```html
<!-- templates/chat.html -->
{% extends "base.html" %}

{% block content %}
<div class="container-fluid h-100 d-flex flex-column">
    <!-- 顶部导航 -->
    <div class="d-flex justify-content-between align-items-center p-3 border-bottom bg-light">
        <button class="btn btn-outline-secondary btn-sm" onclick="goBack()">
            ← 返回
        </button>
        <h5 class="mb-0">智能物流助手</h5>
        <button class="btn btn-outline-primary btn-sm" id="historyBtn" onclick="showHistory()">
            历史记录
        </button>
    </div>

    <!-- 聊天内容区 -->
    <div class="flex-grow-1 overflow-auto p-3" id="chatContainer">
        <div class="text-center text-muted my-5">
            <p>欢迎使用智能物流助手</p>
            <small>您可以：</small><br>
            <small>• 查询物流订单 "查一下最近3天的订单"</small><br>
            <small>• 修改订单状态 "把延误的改成已送达"</small><br>
            <small>• 优化物流线路 "帮我优化下物流"</small><br>
            <small>• 了解物流概念 "什么是SLA"</small>
        </div>
    </div>

    <!-- 历史记录侧边栏 -->
    <div class="position-fixed top-0 end-0 h-100 bg-white border-start shadow"
         id="historySidebar" style="width: 300px; display: none; z-index: 1000;">
        <div class="d-flex justify-content-between align-items-center p-3 border-bottom">
            <h6 class="mb-0">历史记录</h6>
            <button class="btn-close" onclick="hideHistory()"></button>
        </div>
        <div class="p-2">
            <button class="btn btn-primary btn-sm w-100 mb-2" onclick="createNewSession()">
                + 新建对话
            </button>
        </div>
        <div class="overflow-auto" id="sessionList" style="height: calc(100% - 100px);">
            <!-- 会话列表 -->
        </div>
    </div>

    <!-- 确认弹窗 -->
    <div class="modal fade" id="confirmModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">确认操作</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="confirmModalBody">
                    <!-- 动态内容 -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" id="confirmBtn">确认</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Diff 弹窗 -->
    <div class="modal fade" id="diffModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">变更预览</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body" id="diffModalBody">
                    <!-- Diff 表格 -->
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" id="diffConfirmBtn">确认执行</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 输入区 -->
    <div class="border-top p-3 bg-light">
        <div class="input-group">
            <input type="text" class="form-control" id="messageInput"
                   placeholder="输入消息..." onkeypress="handleKeyPress(event)">
            <button class="btn btn-primary" onclick="sendMessage()">发送</button>
        </div>
    </div>
</div>

<script>
let currentSessionId = '{{ session_id if session_id else "" }}';
let pendingPlan = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    if (!currentSessionId) {
        // 检查是否有 URL 参数
        const urlParams = new URLSearchParams(window.location.search);
        currentSessionId = urlParams.get('session_id') || '';
    }

    if (!currentSessionId) {
        // 自动创建新会话
        createNewSession();
    } else {
        // 加载历史消息
        loadHistory();
    }

    loadSessionList();
});

function goBack() {
    window.location.href = '/page/index';
}

function showHistory() {
    document.getElementById('historySidebar').style.display = 'block';
    loadSessionList();
}

function hideHistory() {
    document.getElementById('historySidebar').style.display = 'none';
}

function createNewSession() {
    fetch('/api/chat/sessions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title: '新对话'})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            currentSessionId = data.data.session_id;
            document.getElementById('chatContainer').innerHTML = '';
            hideHistory();
            loadHistory();
        }
    });
}

function loadSessionList() {
    fetch('/api/chat/sessions')
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const list = document.getElementById('sessionList');
            list.innerHTML = '';
            data.data.sessions.forEach(session => {
                const div = document.createElement('div');
                div.className = 'p-2 border-bottom cursor-pointer';
                div.style.cursor = 'pointer';
                div.innerHTML = `
                    <div class="fw-bold">${session.title || '新对话'}</div>
                    <small class="text-muted">${session.message_count} 条消息</small>
                `;
                div.onclick = () => loadSession(session.session_id);
                list.appendChild(div);
            });
        }
    });
}

function loadSession(sessionId) {
    currentSessionId = sessionId;
    window.location.href = '/page/chat/' + sessionId;
}

function loadHistory() {
    if (!currentSessionId) return;

    fetch(`/api/chat/history/${currentSessionId}`)
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const container = document.getElementById('chatContainer');
            container.innerHTML = '';
            data.data.messages.forEach(msg => {
                addMessage(msg.role, msg.content, msg.action_type, msg.diff_content);
            });
            scrollToBottom();
        }
    });
}

function addMessage(role, content, actionType, diffContent) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = 'mb-3';

    if (role === 'user') {
        div.innerHTML = `
            <div class="d-flex justify-content-end">
                <div class="bg-primary text-white p-2 rounded" style="max-width: 70%;">
                    ${escapeHtml(content)}
                </div>
            </div>
        `;
    } else {
        let extra = '';
        if (actionType === 'mutation' && diffContent) {
            try {
                const diff = JSON.parse(diffContent);
                if (diff.before && diff.after) {
                    extra = '<div class="text-muted small mt-1">已执行变更</div>';
                }
            } catch(e) {}
        }
        div.innerHTML = `
            <div class="d-flex justify-content-start">
                <div class="bg-light p-2 rounded border" style="max-width: 70%;">
                    ${escapeHtml(content).replace(/\n/g, '<br>')}
                    ${extra}
                </div>
            </div>
        `;
    }
    container.appendChild(div);
    scrollToBottom();
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;

    if (!currentSessionId) {
        createNewSession().then(() => sendMessageReal(message));
    } else {
        sendMessageReal(message);
    }
}

function sendMessageReal(message) {
    const input = document.getElementById('messageInput');
    input.value = '';

    // 添加用户消息
    addMessage('user', message);

    // 发送请求
    fetch('/api/chat/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id: currentSessionId, message: message})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const result = data.data;
            addMessage('assistant', result.content, result.type);

            if (result.need_confirm && result.action_plan) {
                pendingPlan = result.action_plan;
                showIntentConfirm(result.action_plan);
            }
        } else {
            addMessage('assistant', '抱歉，处理失败: ' + data.message);
        }
    })
    .catch(err => {
        addMessage('assistant', '网络错误，请稍后重试');
    });
}

function showIntentConfirm(plan) {
    const body = document.getElementById('confirmModalBody');
    body.innerHTML = `
        <p>${plan.description || '确认执行此操作？'}</p>
        <p class="text-muted">将影响 ${plan.affected_count} 条记录</p>
    `;

    document.getElementById('confirmBtn').onclick = () => {
        $('#confirmModal').modal('hide');
        confirmIntent();
    };

    $('#confirmModal').modal('show');
}

function confirmIntent() {
    fetch('/api/chat/confirm', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: currentSessionId,
            step: 'intent',
            confirmed: true,
            plan: pendingPlan
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success && data.data.need_diff_confirm) {
            showDiffConfirm(data.data.diff);
        } else {
            addMessage('assistant', data.message || '操作已取消');
        }
    });
}

function showDiffConfirm(diff) {
    const before = diff.before || [];
    const after = diff.after || [];

    let tableHtml = `
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>订单ID</th>
                    <th>原状态</th>
                    <th>新状态</th>
                </tr>
            </thead>
            <tbody>
    `;

    for (let i = 0; i < before.length; i++) {
        tableHtml += `
            <tr>
                <td>${before[i].id}</td>
                <td>${before[i].status}</td>
                <td class="text-success">${after[i]?.status || ''}</td>
            </tr>
        `;
    }

    tableHtml += '</tbody></table>';

    const body = document.getElementById('diffModalBody');
    body.innerHTML = tableHtml;

    document.getElementById('diffConfirmBtn').onclick = () => {
        $('#diffModal').modal('hide');
        confirmDiff();
    };

    $('#diffModal').modal('show');
}

function confirmDiff() {
    fetch('/api/chat/confirm', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: currentSessionId,
            step: 'diff',
            confirmed: true,
            plan: pendingPlan
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            addMessage('assistant', data.data.message || '操作执行成功');
            pendingPlan = null;
            loadHistory();  // 刷新历史
        } else {
            addMessage('assistant', '操作失败: ' + data.message);
        }
    });
}

function scrollToBottom() {
    const container = document.getElementById('chatContainer');
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
</script>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/chat.html
git commit -m "feat: 添加 Agent 对话页面 chat.html"
```

---

## Chunk 6: 数据库迁移

### Task 11: 数据库迁移 SQL

**Files:**
- Create: `docs/superpowers/plans/2026-04-22-agent-dialog-migration.sql`

- [ ] **Step 1: 创建迁移 SQL**

```sql
-- Agent 对话功能数据库迁移脚本
-- 执行时间: 2026-04-22

-- 扩展 chat_history 表
ALTER TABLE chat_history
ADD COLUMN session_id VARCHAR(64) NOT NULL DEFAULT '' COMMENT '会话ID，关联同一轮对话' AFTER page,
ADD COLUMN message_order INT NOT NULL DEFAULT 0 COMMENT '消息顺序' AFTER session_id,
ADD COLUMN action_type VARCHAR(32) DEFAULT NULL COMMENT '动作类型：query/mutation/optimize/explain' AFTER message_order,
ADD COLUMN action_result TEXT DEFAULT NULL COMMENT '执行结果（JSON）' AFTER action_type,
ADD COLUMN diff_content TEXT DEFAULT NULL COMMENT '变更Diff（JSON）' AFTER action_result;

-- 添加索引
ALTER TABLE chat_history ADD INDEX idx_session_id (session_id);
ALTER TABLE chat_history ADD INDEX idx_user_session (user_id, session_id);
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/plans/2026-04-22-agent-dialog-migration.sql
git commit -m "feat: 添加 Agent 对话数据库迁移 SQL"
```

---

## 验证测试

### 测试场景

| 场景 | 测试方法 |
|------|----------|
| 新建对话 | 访问 `/page/chat`，检查是否自动创建 session |
| 发送消息 | 发送"最近3天有多少订单"，检查返回统计 |
| 修改确认 | 发送"把延误的改成已送达"，检查确认弹窗 |
| Diff 展示 | 确认修改后，检查 Diff 弹窗是否显示变更表格 |
| 历史恢复 | 刷新页面，检查消息是否正确加载 |
| 历史列表 | 点击历史记录，检查会话列表是否显示 |
