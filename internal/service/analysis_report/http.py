# pages/analysis_report/http.py
"""分析报告页面 HTTP 处理器"""
from flask import request, render_template

from internal.service.analysis_report.service import AnalysisReportService
from internal.pkg.response import success, error
from internal.middleware import login_required


class AnalysisReportHttp:
    """分析 HTTP 处理器"""

    def __init__(self):
        self.service = AnalysisReportService()

    def routes(self, app):
        """注册分析报告路由"""
        # 页面路由
        app.add_url_rule('/page/analysis_report', endpoint='page_analysis_report', view_func=login_required(self.page_analysis_report))
        # API路由
        app.add_url_rule('/analysis_report', endpoint='get_analysis_report', view_func=login_required(self.get_analysis_report), methods=['GET'])

    def page_analysis_report(self):
        """分析报告页面"""
        return render_template('analysis_report.html')

    def get_analysis_report(self):
        """生成运营分析报告"""
        result = self.service.get_analysis_report()

        if result.get('success'):
            return success(data={
                'analysis': result.get('analysis'),
                'daily_report': result.get('daily_report')
            })
        else:
            return error(result.get('message'))
