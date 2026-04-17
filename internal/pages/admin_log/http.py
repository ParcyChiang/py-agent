# pages/admin_log/http.py
"""管理员日志页面 HTTP 处理器"""
from flask import request

from internal.pages.admin_log.service import LogService
from internal.pkg.response import success, error


class AdminLogHttp:
    """管理员日志页面 HTTP 处理器"""

    def __init__(self):
        self.service = LogService()

    def get_logs(self):
        """获取操作日志"""
        limit = request.args.get('limit', 100, type=int)
        logs = self.service.get_all_logs(limit)
        return success(data={'logs': logs})