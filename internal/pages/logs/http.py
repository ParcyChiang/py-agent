# pages/logs/http.py
"""日志页面 HTTP 处理器"""
from flask import request, render_template

from internal.pages.logs.service import LogService
from internal.pkg.response import success, error
from internal.middleware import login_required, admin_required


class LogsHttp:
    """日志页面 HTTP 处理器"""

    def __init__(self):
        self.service = LogService()

    def routes(self, app):
        """注册日志路由"""
        # 页面路由
        app.add_url_rule(
            '/page/logs',
            endpoint='page_logs',
            view_func=login_required(admin_required(self.page_logs)),
        )
        # API路由
        app.add_url_rule(
            '/api/logs',
            endpoint='api_logs',
            view_func=login_required(admin_required(self.get_logs)),
            methods=['GET']
        )

    def page_logs(self):
        """日志页面"""
        return render_template('logs.html')

    def get_logs(self):
        """获取日志列表"""
        limit = request.args.get('limit', 100, type=int)
        logs = self.service.get_all_logs(limit)
        return success(data={'logs': logs})