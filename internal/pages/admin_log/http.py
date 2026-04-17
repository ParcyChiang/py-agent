# pages/admin_log/http.py
"""管理员日志页面 HTTP 处理器"""
from flask import request, render_template

from internal.pages.admin_log.service import LogService
from internal.pkg.response import success, error
from internal.middleware import login_required, admin_required


class AdminLogHttp:
    """管理员日志页面 HTTP 处理器"""

    def __init__(self):
        self.service = LogService()

    def routes(self, app):
        """注册管理员日志路由"""
        # 页面路由
        app.add_url_rule(
            '/page/admin_log',
            endpoint='page_admin_log',
            view_func=login_required(admin_required(self.page_admin_log)),
        )
        # API路由
        app.add_url_rule(
            '/admin_log',
            endpoint='admin_log',
            view_func=login_required(admin_required(self.get_logs)),
            methods=['GET']
        )

    def page_admin_log(self):
        """管理员日志页面"""
        return render_template('admin_log.html')

    def get_logs(self):
        """获取操作日志"""
        limit = request.args.get('limit', 100, type=int)
        logs = self.service.get_all_logs(limit)
        return success(data={'logs': logs})