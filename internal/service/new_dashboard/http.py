# pages/new_dashboard/http.py
"""动态看板页面 HTTP 处理器"""
from flask import request, render_template

from internal.service.new_dashboard.service import DashboardService
from internal.pkg.response import success, error
from internal.middleware import login_required


class NewDashboardHttp:
    """动态看板 HTTP 处理器"""

    def __init__(self):
        self.service = DashboardService()

    def routes(self, app):
        """注册动态看板路由"""
        # 页面路由
        app.add_url_rule('/page/new_dashboard', endpoint='page_new_dashboard', view_func=login_required(self.page_new_dashboard))
        # API路由
        app.add_url_rule('/api/dashboard/trend', endpoint='dashboard_trend', view_func=login_required(self.get_trend), methods=['GET'])
        app.add_url_rule('/api/dashboard/metrics', endpoint='dashboard_metrics', view_func=login_required(self.get_metrics), methods=['GET'])
        app.add_url_rule('/api/dashboard/table', endpoint='dashboard_table', view_func=login_required(self.get_table), methods=['GET'])

    def page_new_dashboard(self):
        """动态看板页面"""
        return render_template('new_dashboard.html')

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
