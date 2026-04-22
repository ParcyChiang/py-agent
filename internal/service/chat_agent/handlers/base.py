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
