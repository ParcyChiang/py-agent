# pages/analyze/http.py
"""分析页面 HTTP 处理器"""
from flask import request

from internal.pages.analyze.service import AnalyzeService
from internal.pkg.response import success, error


class AnalyzeHttp:
    """分析 HTTP 处理器"""

    def __init__(self):
        self.service = AnalyzeService()

    def get_chart_data(self):
        """获取图表数据（不调用AI）"""
        from internal.pages.upload.service import ShipmentService
        shipment_service = ShipmentService()
        result = shipment_service.get_chart_data()

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('message'))
