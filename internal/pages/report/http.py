# pages/report/http.py
"""报告页面 HTTP 处理器"""
from flask import request

from internal.pages.report.service import ReportService
from internal.pkg.response import success, error


class ReportHttp:
    """报告页面 HTTP 处理器"""

    def __init__(self):
        self.service = ReportService()

    def report(self):
        """分析物流数据"""
        result = self.service.get_report()

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('message'))