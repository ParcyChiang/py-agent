# utils/__init__.py
from datetime import datetime
from typing import Any, Union
import markdown
import pandas as pd


def configure_matplotlib():
    """配置 matplotlib 中文字体和负号显示"""
    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = [
        'Arial Unicode MS', 'SimHei', 'Hiragino Sans GB', 'Heiti SC',
        'STHeiti', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans'
    ]
    plt.rcParams['axes.unicode_minus'] = False


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全地将值转换为 float"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = '') -> str:
    """安全地将值转换为字符串"""
    try:
        if pd.isna(value) or value is None:
            return default
        return str(value)
    except (ValueError, TypeError):
        return default


def safe_date(value: Any) -> Union[str, None]:
    """安全地将值转换为日期字符串"""
    try:
        if pd.isna(value) or value == '' or value is None:
            return None
        return str(value)
    except (ValueError, TypeError):
        return None


def json_serializer(obj: Any) -> Any:
    """JSON序列化辅助函数"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def format_ai_response(response) -> str:
    """格式化AI响应，支持Markdown渲染"""
    # 如果是 AIResponse 对象，转换为字符串
    if hasattr(response, 'text'):
        response = str(response)
    # 使用markdown库正确解析markdown
    html = markdown.markdown(
        response,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    return html