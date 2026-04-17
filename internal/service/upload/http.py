# pages/upload/http.py
"""上传页面 HTTP 处理器"""
from flask import request, session, render_template

from internal.service.upload.service import ShipmentService
from internal.pkg.response import success, error
from internal.middleware import login_required


class UploadHttp:
    """物流 HTTP 处理器"""

    def __init__(self):
        self.service = ShipmentService()

    def routes(self, app):
        """注册上传路由"""
        # 页面路由
        app.add_url_rule('/page/upload', endpoint='page_upload', view_func=login_required(self.page_upload))
        # API路由
        app.add_url_rule('/upload', endpoint='upload_file', view_func=login_required(self.upload), methods=['POST'])
        app.add_url_rule('/delete_csv', endpoint='delete_csv', view_func=login_required(self.delete_csv), methods=['POST'])
        app.add_url_rule('/shipments', endpoint='get_shipments', view_func=self.get_shipments, methods=['GET'])
        app.add_url_rule('/shipment/<shipment_id>', endpoint='get_shipment', view_func=self.get_shipment, methods=['GET'])

    def page_upload(self):
        """上传页面"""
        return render_template('upload.html')

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
        analysis_result = self.service.analyze_shipment(shipment_id)
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