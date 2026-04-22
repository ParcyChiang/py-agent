# pages/compare/http.py
"""物流对比页面 HTTP 处理器"""
import asyncio
import json
import logging
from flask import request, render_template, Response, session

from internal.service.compare.service import CompareService
from internal.pkg.response import success, error
from internal.pkg.dao import ChatHistoryDAO
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class CompareHttp:
    """物流对比页面 HTTP 处理器"""

    def __init__(self):
        self.service = CompareService()
        self.chat_dao = ChatHistoryDAO()

    def routes(self, app):
        """注册物流对比路由"""
        # 页面路由
        app.add_url_rule('/page/compare', endpoint='page_compare', view_func=login_required(self.page_compare))
        # API路由
        app.add_url_rule('/api/shipments/compare', endpoint='compare_data', view_func=login_required(self.get_compare_data), methods=['GET'])
        app.add_url_rule('/api/shipments/filters', endpoint='shipment_filters', view_func=login_required(self.get_filters), methods=['GET'])
        app.add_url_rule('/api/shipments/analyze_comparison_stream', endpoint='analyze_comparison_stream', view_func=login_required(self.analyze_comparison_stream), methods=['POST'])

    def page_compare(self):
        """物流对比页面"""
        return render_template('compare.html')

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

    def analyze_comparison_stream(self):
        """SSE流式分析物流对比数据"""
        # 在请求上下文内提前获取 session 值
        user_id = session.get('user_id') or 0
        username = session.get('username', '游客')

        # 在请求上下文内获取数据
        data = request.get_json()
        comparison_data = data.get('comparison_data', []) if data else []

        def generate():
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def stream_result():
                    full_content = ""  # 累积完整分析内容
                    async for item in self.service.analyze_comparison_stream(comparison_data):
                        if item['type'] == 'thinking':
                            yield f"data: {json.dumps({'type': 'thinking', 'content': item['content']})}\n\n"
                        elif item['type'] == 'text':
                            full_content += item['content']
                            yield f"data: {json.dumps({'type': 'text', 'content': item['content']})}\n\n"
                        elif item['type'] == 'done':
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                            # 保存到对话历史
                            if full_content:
                                try:
                                    self.chat_dao.create_chat(
                                        user_id=user_id,
                                        username=username,
                                        page='compare',
                                        title='物流对比分析 - ' + full_content[:50],
                                        user_input='物流对比分析',
                                        ai_response=full_content
                                    )
                                    logger.info(f"物流对比分析已自动保存到对话历史, user_id={user_id}")
                                except Exception as e:
                                    logger.error(f"保存物流对比分析到对话历史失败: {e}")
                            return
                        elif item['type'] == 'error':
                            yield f"data: {json.dumps({'type': 'error', 'content': item['content']})}\n\n"

                gen = stream_result()
                try:
                    while True:
                        try:
                            chunk = loop.run_until_complete(gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    logger.error(f"流式分析异常: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            finally:
                loop.close()

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
