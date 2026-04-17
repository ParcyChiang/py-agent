# pages/report/http.py
"""报告页面 HTTP 处理器"""
from flask import request, render_template

from internal.pages.report.service import ReportService
from internal.pkg.response import success, error
from internal.middleware import login_required


class ReportHttp:
    """报告页面 HTTP 处理器"""

    def __init__(self):
        self.service = ReportService()

    def routes(self, app):
        """注册报告路由"""
        # 页面路由
        app.add_url_rule('/page/report', endpoint='page_report', view_func=login_required(self.page_report))
        # API路由
        app.add_url_rule('/report', endpoint='report', view_func=login_required(self.report), methods=['GET'])

    def page_report(self):
        """报告页面"""
        return render_template('report.html')

    def report(self):
        """生成今日日报"""
        result = self.service.get_report()

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('message'))