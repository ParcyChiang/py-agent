#辅助函数
import json
from datetime import datetime
from typing import Any, Dict


def json_serializer(obj: Any) -> Any:
    """JSON序列化辅助函数"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def format_ai_response(response: str) -> str:
    """格式化AI响应"""
    # 将响应中的编号项目转换为HTML列表
    lines = response.split('\n')
    html_lines = []

    for line in lines:
        if line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            html_lines.append(f'<li>{line[2:].strip()}</li>')
        elif line.strip().startswith('- '):
            html_lines.append(f'<li>{line[2:].strip()}</li>')
        else:
            html_lines.append(f'<p>{line}</p>')

    # 将连续列表项包装在<ul>标签中
    html_content = []
    in_list = False

    for line in html_lines:
        if '<li>' in line:
            if not in_list:
                html_content.append('<ul>')
                in_list = True
            html_content.append(line)
        else:
            if in_list:
                html_content.append('</ul>')
                in_list = False
            html_content.append(line)

    if in_list:
        html_content.append('</ul>')

    return ''.join(html_content)