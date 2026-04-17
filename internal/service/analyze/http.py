# pages/analyze/http.py
"""分析页面 HTTP 处理器"""
from flask import request, render_template

from internal.service.analyze.service import AnalyzeService
from internal.pkg.response import success, error
from internal.middleware import login_required


class AnalyzeHttp:
    """分析 HTTP 处理器"""

    def __init__(self):
        self.service = AnalyzeService()

    def routes(self, app):
        """注册分析路由"""
        # 页面路由
        app.add_url_rule('/page/analyze', endpoint='page_analyze', view_func=login_required(self.page_analyze))
        # API路由
        app.add_url_rule('/chart_data', endpoint='analyze_chart_data', view_func=login_required(self.get_chart_data), methods=['GET'])

    def page_analyze(self):
        """分析页面"""
        return render_template('analyze.html')

    def get_chart_data(self):
        """获取图表数据（不调用AI）"""
        from internal.service.upload.service import ShipmentService
        shipment_service = ShipmentService()
        result = shipment_service.get_chart_data()

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('message'))
