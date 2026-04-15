# internal/server/shipment.py
"""物流业务逻辑层"""
from typing import Dict, List, Any, Tuple

from internal.models.shipment import ShipmentDAO
from internal.models.log import LogDAO
from internal.pkg.charts import generate_chart_data


class ShipmentService:
    """物流业务服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.log_dao = LogDAO()

    def import_csv(self, file_bytes: bytes, user_id: int = None, username: str = None, ip_address: str = None) -> Dict[str, Any]:
        """导入 CSV 数据"""
        result = self.shipment_dao.import_from_csv_bytes(file_bytes)

        if result.get('success') and user_id:
            count = result.get('count', 0)
            self.log_dao.add_log(
                user_id,
                username or '',
                '数据上传',
                f'上传CSV文件，导入{count}条记录',
                ip_address or ''
            )

        return result

    def clear_all_data(self, user_id: int = None, username: str = None, ip_address: str = None) -> Dict[str, Any]:
        """清空所有数据"""
        try:
            self.shipment_dao.clear_all_data()

            if user_id:
                self.log_dao.add_log(
                    user_id,
                    username or '',
                    '清空数据',
                    '清空所有CSV导入数据',
                    ip_address or ''
                )

            return {'success': True, 'message': '已清空所有CSV导入数据'}
        except Exception as e:
            return {'success': False, 'message': f'清空失败: {str(e)}'}

    def get_shipments(self, limit: int = 10000, page: int = None, pageSize: int = None) -> Tuple[List[Dict], int]:
        """获取物流列表"""
        return self.shipment_dao.get_all_shipments(limit, page, pageSize)

    def get_shipment_by_id(self, shipment_id: str) -> Tuple[Dict, List[Dict]]:
        """获取单个物流详情"""
        shipment = self.shipment_dao.get_shipment_by_id(shipment_id)
        if not shipment:
            return None, []

        events = self.shipment_dao.get_shipment_events(shipment_id)
        return shipment, events

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
        status_distribution = self.get_status_distribution()

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

    def get_status_distribution(self) -> Dict[str, int]:
        """获取状态分布"""
        from collections import Counter
        from internal.pkg.constants import STATUS_CN_MAP

        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)
        distribution = {}

        for shipment in shipments:
            status = shipment.get('status', 'unknown')
            cn_status = STATUS_CN_MAP.get(status, status)
            distribution[cn_status] = distribution.get(cn_status, 0) + 1

        return distribution
