# pages/report/http.py
"""报告页面 HTTP 处理器"""
import asyncio
import json
import logging
from flask import request, render_template, Response, session

from internal.service.report.service import ReportService
from internal.pkg.response import success, error
from internal.pkg.dao import ChatHistoryDAO
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class ReportHttp:
    """报告页面 HTTP 处理器"""

    def __init__(self):
        self.service = ReportService()
        self.chat_dao = ChatHistoryDAO()

    def routes(self, app):
        """注册报告路由"""
        # 页面路由
        app.add_url_rule('/page/report', endpoint='page_report', view_func=login_required(self.page_report))
        # API路由
        app.add_url_rule('/report_stream', endpoint='report_stream', view_func=login_required(self.report_stream), methods=['GET'])

    def page_report(self):
        """报告页面"""
        return render_template('report.html')

    def report_stream(self):
        """SSE流式生成日报"""
        # 在请求上下文内提前获取 session 值
        user_id = session.get('user_id') or 0
        username = session.get('username', '游客')

        def generate():
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def stream_result():
                    async for item in self.service.generate_report_stream_with_format():
                        if item['type'] == 'thinking':
                            yield f"data: {json.dumps({'type': 'thinking', 'content': item['content']})}\n\n"
                        elif item['type'] == 'text':
                            yield f"data: {json.dumps({'type': 'text', 'content': item['content']})}\n\n"
                        elif item['type'] == 'done':
                            yield f"data: {json.dumps({'type': 'done', 'content': item['content']})}\n\n"
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                            return
                        elif item['type'] == 'error':
                            yield f"data: {json.dumps({'type': 'error', 'content': item['content']})}\n\n"

                gen = stream_result()
                full_content = None
                try:
                    while True:
                        try:
                            chunk = loop.run_until_complete(gen.__anext__())
                            # 捕获 done 类型的内容用于后续入库
                            if full_content is None and 'done' in chunk:
                                try:
                                    data = json.loads(chunk.split('data: ')[1].split('\n')[0])
                                    if data.get('type') == 'done':
                                        full_content = data.get('content', '')
                                except:
                                    pass
                            yield chunk
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    logger.error(f"流式生成日报异常: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

                # 流结束后，保存到对话历史
                if full_content:
                    try:
                        self.chat_dao.create_chat(
                            user_id=user_id,
                            username=username,
                            page='report',
                            title='日报中心 - ' + self.service.shipment_dao.get_daily_stats().get('date', '未知'),
                            user_input='生成日报',
                            ai_response=full_content
                        )
                        logger.info(f"日报已自动保存到对话历史, user_id={user_id}")
                    except Exception as e:
                        logger.error(f"保存日报到对话历史失败: {e}")
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