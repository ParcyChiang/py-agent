# pages/analyze/service.py
"""分析页面服务层"""
from typing import Dict, Any

from internal.service.upload.dao import ShipmentDAO


class AnalyzeService:
    """分析服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()

    def get_chart_data(self) -> Dict[str, Any]:
        """获取图表数据"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {
                'success': False,
                'message': '没有可分析的数据，请先上传CSV文件'
            }

        daily_stats = self.shipment_dao.get_daily_stats()
        daily_trend = self.shipment_dao.get_daily_trend()
        status_distribution = self._get_status_distribution()

        from internal.pkg.charts import generate_chart_data
        chart_data = generate_chart_data(shipments, daily_stats)

        return {
            'success': True,
            'summary': {
                'status_distribution': status_distribution
            },
            'statistics': {
                'total_shipments': daily_stats.get('total_shipments', len(shipments)),
                'surface_3d': chart_data['surface_3d'],
                'scatter_3d': chart_data['scatter_3d'],
                'wireframe_3d': chart_data['wireframe_3d'],
                'data_info': chart_data['data_info'],
                'daily_trend': daily_trend
            }
        }

    def _get_status_distribution(self) -> Dict[str, int]:
        """获取状态分布"""
        from internal.pkg.constants import STATUS_CN_MAP

        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)
        distribution = {}

        for shipment in shipments:
            status = shipment.get('status', 'unknown')
            cn_status = STATUS_CN_MAP.get(status, status)
            distribution[cn_status] = distribution.get(cn_status, 0) + 1

        return distribution