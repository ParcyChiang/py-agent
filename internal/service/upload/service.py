# pages/upload/service.py
"""上传页面服务层"""
from typing import Dict, List, Any, Tuple

from internal.pkg.dao import ShipmentDAO, LogDAO


class ShipmentService:
    """物流服务"""

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