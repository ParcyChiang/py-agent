# pages/report/service.py
"""报告页面服务层"""
import asyncio
from typing import Dict, Any

from internal.service.upload.dao import ShipmentDAO
from internal.pkg.models.model_handler import AIModelHandler
from internal.pkg.utils import format_ai_response


class ReportService:
    """AI分析服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = AIModelHandler()

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

    async def generate_report_stream(self):
        """流式生成日报"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            yield {'type': 'error', 'content': '没有可分析的数据，请先上传CSV文件'}
            return

        daily_stats = self.shipment_dao.get_daily_stats()

        prompt = f"""
生成今日日报：

核心统计：
- 发货 {daily_stats.get('total_shipments', 0)}，交付 {daily_stats.get('delivered', 0)}，
  延迟 {daily_stats.get('delayed', 0)}，准时率 {daily_stats.get('on_time_rate', 0):.1f}%

请严格按以下结构输出（短句要点式）：
A. 今日运行态势（拥堵/异常波次/高峰时段）
B. 风险清单（TOP3：场地、车辆、干线/支线）
C. 产能与人力（分拣线利用率、缺口岗位与时段）
D. 关键KPI（SLA命中率、滞留件、问题件、装车准点）
E. 行动清单（≤5条，明确"责任岗位+完成时限"）
"""

        async for chunk in self.model_handler.generate_response_stream(prompt, ""):
            if chunk['type'] in ('thinking', 'text', 'error'):
                yield chunk

        yield {'type': 'done'}
