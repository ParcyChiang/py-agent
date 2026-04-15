# internal/handler/dashboard.py
"""动态看板 HTTP 处理器"""
from flask import request

from internal.server import DashboardService
from internal.pkg.response import success, error


class DashboardHandler:
    """动态看板 HTTP 处理器"""

    def __init__(self):
        self.service = DashboardService()

    def get_trend(self):
        """获取趋势数据"""
        granularity = request.args.get('granularity', 'realtime')
        result = self.service.get_trend_data(granularity)

        if result.get('success'):
            return success(data={'data': result.get('data')})
        else:
            return error(result.get('message'))

    def get_metrics(self):
        """获取指标数据"""
        result = self.service.get_metrics()

        if result.get('success'):
            return success(data={'data': result.get('data')})
        else:
            return error(result.get('message'))

    def get_table(self):
        """获取表格数据"""
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 10, type=int)
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '')
        sortField = request.args.get('sortField', 'time')
        sortDirection = request.args.get('sortDirection', 'desc')

        result = self.service.get_table_data(
            page=page,
            pageSize=pageSize,
            status_filter=status_filter,
            search=search,
            sortField=sortField,
            sortDirection=sortDirection
        )

        if result.get('success'):
            return success(data={
                'data': result.get('data'),
                'total': result.get('total'),
                'page': result.get('page'),
                'pageSize': result.get('pageSize')
            })
        else:
            return error(result.get('message'))
