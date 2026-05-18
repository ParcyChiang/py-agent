# pages/map/http.py
"""地图页面 HTTP 处理器"""
from flask import render_template, request

from internal.configs.config import Config
from internal.service.upload.service import ShipmentService
from internal.pkg.response import success
from internal.middleware import login_required


class MapHttp:
    """地图页面 HTTP 处理器"""

    def __init__(self):
        self.shipment_service = ShipmentService()

    def routes(self, app):
        """注册地图路由"""
        app.add_url_rule('/page/map', endpoint='page_map', view_func=login_required(self.page_map))
        app.add_url_rule('/api/map/shipments', endpoint='get_map_shipments', view_func=login_required(self.get_shipments), methods=['GET'])

    def page_map(self):
        """地图页面"""
        return render_template('map.html', amap_api_key=Config.AMAP_API_KEY, amap_geo_key=Config.AMAP_GEO_KEY)

    def get_shipments(self):
        """获取用于地图展示的物流数据"""
        city = request.args.get('city', '杭州')  # 默认杭州
        shipments, _ = self.shipment_service.get_shipments(limit=1000)
        # 过滤与该城市相关的物流（起点或终点）
        filtered = [s for s in shipments if s.get('origin_city') == city or s.get('destination_city') == city]
        # 限制条数（默认100）
        filtered = filtered[:Config.MAP_SHIPMENT_LIMIT]
        data = [{
            'id': s.get('id'),
            'origin': s.get('origin'),
            'origin_city': s.get('origin_city'),
            'destination': s.get('destination'),
            'destination_city': s.get('destination_city'),
            'status': s.get('status'),
            'courier_company': s.get('courier_company'),
        } for s in filtered]
        return success(data={'data': data})
