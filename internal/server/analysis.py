# internal/server/analysis.py
"""AI 分析业务逻辑层"""
import asyncio
from typing import Dict, Any, List

from internal.models.shipment import ShipmentDAO
from internal.models.model_handler import MiniMaxModelHandler
from internal.pkg.charts import generate_chart_data
from internal.pkg.utils import format_ai_response


class AnalysisService:
    """AI 分析业务服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = MiniMaxModelHandler()

    def analyze_data(self) -> Dict[str, Any]:
        """分析物流数据"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {
                'success': False,
                'message': '没有可分析的数据，请先上传CSV文件'
            }

        daily_stats = self.shipment_dao.get_daily_stats()
        daily_trend = self.shipment_dao.get_daily_trend()

        # 使用 AI 分析数据
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

        # 格式化响应
        analysis_html = format_ai_response(analysis['analysis'])
        report_html = format_ai_response(daily_report['report'])

        # 生成图表数据
        chart_data = generate_chart_data(shipments, daily_stats)

        return {
            'success': True,
            'analysis': analysis_html,
            'daily_report': report_html,
            'statistics': {
                **daily_stats,
                'surface_3d': chart_data['surface_3d'],
                'scatter_3d': chart_data['scatter_3d'],
                'wireframe_3d': chart_data['wireframe_3d'],
                'data_info': chart_data['data_info'],
                'daily_trend': daily_trend
            },
            'summary': {
                'total_records': len(shipments),
                'status_distribution': self.model_handler._get_status_distribution(shipments)
            }
        }

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

    def analyze_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """分析单个物流"""
        shipment = self.shipment_dao.get_shipment_by_id(shipment_id)
        if not shipment:
            return {
                'success': False,
                'message': '未找到指定的物流信息'
            }

        events = self.shipment_dao.get_shipment_events(shipment_id)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis = loop.run_until_complete(
                self.model_handler.analyze_shipment_data(shipment)
            )
            prediction = loop.run_until_complete(
                self.model_handler.predict_delivery_time(shipment, events)
            )
        finally:
            loop.close()

        analysis_html = format_ai_response(analysis['analysis'])
        prediction_html = format_ai_response(prediction['prediction'])

        return {
            'success': True,
            'shipment': shipment,
            'events': events,
            'analysis': analysis_html,
            'prediction': prediction_html
        }
