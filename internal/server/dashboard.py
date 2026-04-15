# internal/server/dashboard.py
"""动态看板业务逻辑层"""
from datetime import datetime, timedelta
from typing import Dict, List, Any

from internal.models.shipment import ShipmentDAO


class DashboardService:
    """动态看板业务服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()

    def get_trend_data(self, granularity: str = 'realtime') -> Dict[str, Any]:
        """获取趋势数据"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {'success': False, 'message': '没有可用的数据'}

        trend_data = []
        now = datetime.now()

        if granularity == 'realtime':
            points = 60
            interval = 1
        elif granularity == '1min':
            points = 60
            interval = 60
        else:
            points = 60
            interval = 300

        for i in range(points):
            time = now - timedelta(seconds=i * interval)
            base_value = len(shipments) // 100
            random_factor = (hash(str(time)) % 100) / 100
            value = base_value + int(random_factor * 100)

            trend_data.append({
                'time': time.strftime('%H:%M:%S'),
                'value': value
            })

        return {
            'success': True,
            'data': trend_data[::-1]
        }

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标数据"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {'success': False, 'message': '没有可用的数据'}

        total = len(shipments)
        delivered = sum(1 for s in shipments if s.get('status') == 'delivered')
        in_transit = sum(1 for s in shipments if s.get('status') == 'in_transit')
        delivery_rate = (delivered / total * 100) if total > 0 else 0

        delivery_times = []
        for s in shipments:
            if s.get('actual_delivery') and s.get('created_at'):
                try:
                    created = datetime.fromisoformat(str(s['created_at']).replace('Z', '+00:00'))
                    delivered_time = datetime.fromisoformat(str(s['actual_delivery']).replace('Z', '+00:00'))
                    hours = (delivered_time - created).total_seconds() / 3600
                    delivery_times.append(hours)
                except:
                    pass

        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0

        warehouse_efficiency = 75 + (hash(str(datetime.now())) % 20)
        exception_rate = 5 + (hash(str(datetime.now())) % 10)

        def generate_trend():
            return round((hash(str(datetime.now())) % 200 - 100) / 10, 1)

        metrics = [
            {
                'name': '今日交付',
                'value': delivered,
                'trend': generate_trend(),
                'trendUp': hash(str(datetime.now())) % 2 == 0
            },
            {
                'name': '运输中',
                'value': in_transit,
                'trend': generate_trend(),
                'trendUp': hash(str(datetime.now())) % 2 == 0
            },
            {
                'name': '交付率',
                'value': f'{delivery_rate:.1f}%',
                'trend': generate_trend(),
                'trendUp': hash(str(datetime.now())) % 2 == 0
            },
            {
                'name': '平均时效',
                'value': f'{avg_delivery_time:.1f}小时',
                'trend': generate_trend(),
                'trendUp': hash(str(datetime.now())) % 2 == 1
            },
            {
                'name': '中转仓效率',
                'value': f'{warehouse_efficiency:.1f}%',
                'trend': generate_trend(),
                'trendUp': hash(str(datetime.now())) % 2 == 0
            },
            {
                'name': '异常率',
                'value': f'{exception_rate:.1f}%',
                'trend': generate_trend(),
                'trendUp': hash(str(datetime.now())) % 2 == 1
            }
        ]

        return {
            'success': True,
            'data': metrics
        }

    def get_table_data(
        self,
        page: int = 1,
        pageSize: int = 10,
        status_filter: str = 'all',
        search: str = '',
        sortField: str = 'time',
        sortDirection: str = 'desc'
    ) -> Dict[str, Any]:
        """获取表格数据"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {'success': False, 'message': '没有可用的数据'}

        status_map = {
            'delivered': '已交付',
            'in_transit': '运输中',
            'pending': '待处理',
            'out_for_delivery': '派件中',
            'picked_up': '已揽件',
            'processing': '处理中',
            'failed_delivery': '配送失败',
            'returned': '已退回'
        }

        table_data = []
        for s in shipments:
            status_cn = status_map.get(s.get('status'), s.get('status', '未知'))

            table_data.append({
                'orderId': s.get('id', ''),
                'company': s.get('courier_company', '未知'),
                'status': status_cn,
                'origin': s.get('origin_city', s.get('origin', '未知')),
                'destination': s.get('destination_city', s.get('destination', '未知')),
                'time': s.get('created_at', ''),
                'value': str(s.get('shipping_fee', 0))
            })

        if status_filter != 'all':
            table_data = [d for d in table_data if d['status'] == status_filter]

        if search:
            search_lower = search.lower()
            table_data = [d for d in table_data
                         if search_lower in d['orderId'].lower() or
                            search_lower in d['company'].lower()]

        reverse = sortDirection == 'desc'
        try:
            table_data.sort(key=lambda x: x.get(sortField, ''), reverse=reverse)
        except:
            pass

        total = len(table_data)
        start = (page - 1) * pageSize
        end = start + pageSize
        page_data = table_data[start:end]

        return {
            'success': True,
            'data': page_data,
            'total': total,
            'page': page,
            'pageSize': pageSize
        }
