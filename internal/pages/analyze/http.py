# pages/analyze/http.py
"""分析页面 HTTP 处理器"""
from flask import request

from internal.pages.analyze.service import AnalysisService
from internal.pkg.response import success, error


class AnalyzeHttp:
    """分析 HTTP 处理器"""

    def __init__(self):
        self.service = AnalysisService()

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

    def get_chart_data(self):
        """获取图表数据（不调用AI）"""
        from internal.pages.upload.service import ShipmentService
        shipment_service = ShipmentService()
        result = shipment_service.get_chart_data()

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('message'))
