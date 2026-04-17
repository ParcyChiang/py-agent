# pages/report/service.py
"""报告页面服务层"""
import asyncio
from typing import Dict, Any

from internal.pages.upload.dao import ShipmentDAO
from internal.models.model_handler import MiniMaxModelHandler
from internal.pkg.utils import format_ai_response


class ReportService:
    """AI分析服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = MiniMaxModelHandler()

    def get_report(self) -> Dict[str, Any]:
        """生成日报"""
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
            daily_report = loop.run_until_complete(
                self.model_handler.generate_daily_report(daily_stats, shipments)
            )
        finally:
            loop.close()

        report_html = format_ai_response(daily_report['report'])

        return {
            'success': True,
            'daily_report': report_html
        }
