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

    async def process_stream(self, message: str, context: List[Dict]):
        """流式处理用户消息"""
        # 1. 流式意图识别
        intent_type = ""
        async for chunk in self._detect_intent_stream(message):
            if chunk['type'] == 'text':
                intent_type += chunk['content']
            yield chunk

        intent_type = intent_type.strip().lower()
        if intent_type not in ('query', 'mutation', 'optimize', 'explain'):
            intent_type = 'explain'

        # 2. 流式参数提取
        params_text = ""
        async for chunk in self._extract_params_stream(message):
            if chunk['type'] == 'text':
                params_text += chunk['content']
            yield chunk

        try:
            params_text = re.sub(r'```json\s*', '', params_text)
            params_text = re.sub(r'```\s*', '', params_text)
            params = json.loads(params_text.strip())
        except:
            params = {}

        # 3. 构建意图对象
        intent = {
            'type': intent_type,
            'message': message,
            'params': params
        }

        # 4. 路由到 Handler 进行流式处理
        handler = self.handlers.get(intent_type)
        if handler and hasattr(handler, 'handle_stream'):
            async for chunk in handler.handle_stream(intent, context):
                yield chunk
        elif handler:
            # Handler 不支持流式，降级为普通处理
            response = await handler.handle(intent, context)
            yield {'type': 'text', 'content': response.content}
            if response.need_confirm:
                yield {'type': 'need_confirm', 'action_plan': response.action_plan}
        else:
            yield {'type': 'error', 'content': '无法处理此请求'}

    async def _detect_intent_stream(self, message: str):
        """流式识别用户意图"""
        prompt = self.INTENT_PROMPT.format(message=message)
        try:
            async for chunk in self.model.generate_response_stream(prompt, ""):
                yield chunk
        except Exception as e:
            yield {'type': 'text', 'content': 'explain'}

    async def _extract_params_stream(self, message: str):
        """流式提取参数"""
        prompt = self.PARAM_EXTRACT_PROMPT.format(message=message)
        try:
            async for chunk in self.model.generate_response_stream(prompt, ""):
                yield chunk
        except Exception as e:
            yield {'type': 'text', 'content': '{}'}
