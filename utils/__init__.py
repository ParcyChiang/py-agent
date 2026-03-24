# utils/__init__.py
from datetime import datetime
from typing import Any
import markdown


def json_serializer(obj: Any) -> Any:
    """JSON序列化辅助函数"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def format_ai_response(response: str) -> str:
    """格式化AI响应，支持Markdown渲染"""
    # 使用markdown库正确解析markdown
    html = markdown.markdown(
        response,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    return html