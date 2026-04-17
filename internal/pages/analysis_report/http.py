# pages/analysis_report/http.py
"""分析报告页面 HTTP 处理器"""
from flask import request

from internal.pages.analysis_report.service import AnalysisReportService
from internal.pkg.response import success, error


class AnalysisReportHttp:
    """分析 HTTP 处理器"""

    def __init__(self):
        self.service = AnalysisReportService()

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
