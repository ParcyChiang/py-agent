# pages/compare/http.py
"""物流对比页面 HTTP 处理器"""
from flask import request

from internal.pages.compare.service import CompareService
from internal.pkg.response import success, error


class CompareHttp:
    """物流对比页面 HTTP 处理器"""

    def __init__(self):
        self.service = CompareService()

    def get_compare_data(self):
        """对比同一收件地址或发件地址的物流信息"""
        origin_filter = request.args.get('origin', '')
        destination_filter = request.args.get('destination', '')
        courier_filter = request.args.get('courier', '')
        page = request.args.get('page', 1, type=int)
        pageSize = request.args.get('pageSize', 20, type=int)

        return self.service.get_compare_data(
            origin_filter=origin_filter,
            destination_filter=destination_filter,
            courier_filter=courier_filter,
            page=page,
            pageSize=pageSize
        )

    def get_filters(self):
        """获取物流筛选过滤选项"""
        return self.service.get_filters()

    async def analyze_comparison(self):
        """使用LLM分析物流对比数据"""
        data = request.get_json()
        comparison_data = data.get('comparison_data', [])
        return await self.service.analyze_comparison(comparison_data)
