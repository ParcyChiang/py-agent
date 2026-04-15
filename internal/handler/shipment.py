# internal/handler/shipment.py
"""物流 HTTP 处理器"""
from flask import request, session

from internal.server import ShipmentService
from internal.pkg.response import success, error


class ShipmentHandler:
    """物流 HTTP 处理器"""

    def __init__(self):
        self.service = ShipmentService()

    def get_shipments(self):
        """获取物流列表"""
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 10, type=int)
        limit = request.args.get('limit', None, type=int)

        if limit is not None:
            shipments = self.service.get_shipments(limit=limit)
            if isinstance(shipments, tuple):
                shipments = shipments[0]
            return success(data={'data': shipments, 'total': len(shipments)})

        shipments, total = self.service.get_shipments(page=page, pageSize=pageSize)
        return success(data={'data': shipments, 'total': total, 'page': page, 'pageSize': pageSize})

    def get_shipment(self, shipment_id):
        """获取单个物流详情"""
        from internal.server import AnalysisService

        shipment, events = self.service.get_shipment_by_id(shipment_id)
        if not shipment:
            return error('未找到指定的物流信息', 404)

        analysis_service = AnalysisService()
        analysis_result = analysis_service.analyze_shipment(shipment_id)

        return success(data=analysis_result)

    def upload(self):
        """上传 CSV 文件"""
        if 'file' not in request.files:
            return error('没有选择文件')

        file = request.files['file']
        if file.filename == '':
            return error('没有选择文件')

        if not file.filename.lower().endswith('.csv'):
            return error('只支持CSV文件')

        file_bytes = file.read()
        user_id = session.get('user_id')
        username = session.get('username')

        result = self.service.import_csv(
            file_bytes,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr
        )

        if result.get('success'):
            return success(message=result.get('message'), data={'count': result.get('count')})
        else:
            return error(result.get('message'))

    def delete_csv(self):
        """清空所有数据"""
        user_id = session.get('user_id')
        username = session.get('username')

        result = self.service.clear_all_data(
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr
        )

        if result.get('success'):
            return success(message=result.get('message'))
        else:
            return error(result.get('message'))

    def get_chart_data(self):
        """获取图表数据"""
        result = self.service.get_chart_data()

        if result.get('success'):
            shipments, _ = self.service.get_shipments(limit=10000)
            from internal.server import AnalysisService
            analysis_service = AnalysisService()

            return success(data={
                'statistics': result.get('statistics'),
                'summary': {
                    'total_records': len(shipments),
                    'status_distribution': analysis_service.model_handler._get_status_distribution(shipments)
                }
            })
        else:
            return error(result.get('message'))
