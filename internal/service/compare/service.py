# pages/compare/service.py
"""物流对比页面服务层"""
import asyncio
from datetime import datetime
from typing import Dict, Any

from internal.pkg.dao import ShipmentDAO
from internal.pkg.models.model_handler import AIModelHandler


class CompareService:
    """物流对比服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = AIModelHandler()

    def get_compare_data(self, origin_filter: str = '', destination_filter: str = '', courier_filter: str = '', page: int = 1, pageSize: int = 20) -> Dict[str, Any]:
        """对比同一收件地址或发件地址的物流信息"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            return {'success': False, 'message': '没有可用的数据'}

        # 过滤
        filtered_shipments = []
        for shipment in shipments:
            origin = shipment.get('origin', '')
            destination = shipment.get('destination', '')
            courier = shipment.get('courier_company', '')

            if origin_filter and origin_filter not in origin:
                continue
            if destination_filter and destination_filter not in destination:
                continue
            if courier_filter and courier_filter not in courier:
                continue

            filtered_shipments.append(shipment)

        # 按地址分组
        address_groups = {}
        for shipment in filtered_shipments:
            destination = shipment.get('destination', '')
            if destination:
                if destination not in address_groups:
                    address_groups[destination] = {'type': 'destination', 'shipments': []}
                address_groups[destination]['shipments'].append(shipment)

            origin = shipment.get('origin', '')
            if origin:
                if origin not in address_groups:
                    address_groups[origin] = {'type': 'origin', 'shipments': []}
                address_groups[origin]['shipments'].append(shipment)

        # 过滤出有两条以上记录的地址
        valid_groups = {addr: grp for addr, grp in address_groups.items() if len(grp['shipments']) >= 2}

        # 分析
        comparison_results = []
        for address, group in valid_groups.items():
            shipments_list = group['shipments']

            delivery_times = []
            for shipment in shipments_list:
                if shipment.get('actual_delivery') and shipment.get('created_at'):
                    try:
                        created = datetime.fromisoformat(str(shipment['created_at']).replace('Z', '+00:00'))
                        delivered = datetime.fromisoformat(str(shipment['actual_delivery']).replace('Z', '+00:00'))
                        hours = (delivered - created).total_seconds() / 3600
                        delivery_times.append(hours)
                    except:
                        pass

            avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0

            status_counts = {}
            for shipment in shipments_list:
                status = shipment.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            courier_counts = {}
            for shipment in shipments_list:
                courier = shipment.get('courier_company', 'unknown')
                courier_counts[courier] = courier_counts.get(courier, 0) + 1

            total_fee = sum(shipment.get('shipping_fee', 0) for shipment in shipments_list)
            avg_fee = total_fee / len(shipments_list) if shipments_list else 0

            comparison_results.append({
                'address': address,
                'address_type': group['type'],
                'shipment_count': len(shipments_list),
                'avg_delivery_time': avg_delivery_time,
                'status_distribution': status_counts,
                'courier_distribution': courier_counts,
                'avg_shipping_fee': avg_fee,
                'shipments': shipments_list
            })

        comparison_results.sort(key=lambda x: x['shipment_count'], reverse=True)

        total = len(comparison_results)
        start = (page - 1) * pageSize
        end = start + pageSize
        page_data = comparison_results[start:end]

        return {'success': True, 'data': page_data, 'total': total, 'page': page, 'pageSize': pageSize}

    def get_filters(self) -> Dict[str, Any]:
        """获取物流筛选过滤选项"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        origins = sorted(list(set(s.get('origin', '') for s in shipments if s.get('origin'))))
        destinations = sorted(list(set(s.get('destination', '') for s in shipments if s.get('destination'))))
        couriers = sorted(list(set(s.get('courier_company', '') for s in shipments if s.get('courier_company'))))

        return {'success': True, 'origins': origins, 'destinations': destinations, 'couriers': couriers}

    async def analyze_comparison_stream(self, comparison_data: list):
        """使用LLM流式分析物流对比数据"""
        if not comparison_data:
            yield {'type': 'error', 'content': '没有提供对比数据'}
            return

        prompt = f"""
        你是一个物流运营专家，需要对以下物流对比数据进行分析并给出优化方案：

        {comparison_data}

        请按照以下结构输出分析结果：
        1. 数据概览：总结对比情况
        2. 关键发现：识别出的问题和异常情况
        3. 优化方案：针对发现的问题给出具体的优化建议
        4. 实施优先级：对优化方案进行优先级排序

        分析要具体、可操作，基于实际物流运营场景。
        """

        async for chunk in self.model_handler.generate_response_stream(prompt, ""):
            if chunk['type'] in ('thinking', 'text', 'error'):
                yield chunk

        yield {'type': 'done'}
