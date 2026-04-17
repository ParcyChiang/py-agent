# pages/logs/http.py
"""日志页面 HTTP 处理器"""
from flask import request

from internal.pages.logs.service import LogService
from internal.pkg.response import success, error


class LogsHttp:
    """日志页面 HTTP 处理器"""

    def __init__(self):
        self.service = LogService()

    def get_logs(self):
        """获取日志列表"""
        limit = request.args.get('limit', 100, type=int)
        logs = self.service.get_all_logs(limit)
        return success(data={'logs': logs})