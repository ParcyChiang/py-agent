# pages/analysis_report/service.py
"""分析报告页面服务层"""
import asyncio
from typing import Dict, Any

from internal.pages.upload.dao import ShipmentDAO
from internal.models.model_handler import MiniMaxModelHandler
from internal.pkg.utils import format_ai_response


class AnalysisReportService:
    """AI分析服务"""
    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = MiniMaxModelHandler()

    def get_analysis_report(self) -> Dict[str, Any]:
        """生成运营分析报告"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {
                'success': False,
                'message': '没有可分析的数据，请先上传CSV文件'
            }

        daily_stats = self.shipment_dao.get_daily_stats()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis = loop.run_until_complete(
                self.model_handler.analyze_bulk_data(shipments)
            )
            daily_report = loop.run_until_complete(
                self.model_handler.generate_daily_report(daily_stats, shipments)
            )
        finally:
            loop.close()

        analysis_html = format_ai_response(analysis['analysis'])
        report_html = format_ai_response(daily_report['report'])

        return {
            'success': True,
            'analysis': analysis_html,
            'daily_report': report_html
        }
