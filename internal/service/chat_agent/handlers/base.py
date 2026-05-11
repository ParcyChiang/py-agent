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

    async def handle_stream(self, intent: Dict, context: List[Dict]):
        """流式处理请求"""
        # 默认实现：调用 handle 并 yield 完整内容
        response = await self.handle(intent, context)
        yield {'type': 'text', 'content': response.content}
        if response.need_confirm:
            yield {'type': 'need_confirm', 'action_plan': response.action_plan}

    def parse_result(self, result_text: str, key: str, default=None):
        """简单解析 JSON 结果"""
        try:
            data = json.loads(result_text)
            return data.get(key, default)
        except:
            return default
