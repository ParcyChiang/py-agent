# pages/report/http.py
"""报告页面 HTTP 处理器"""
import asyncio
import json
import logging
from flask import request, render_template, Response

from internal.service.report.service import ReportService
from internal.pkg.response import success, error
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class ReportHttp:
    """报告页面 HTTP 处理器"""

    def __init__(self):
        self.service = ReportService()

    def routes(self, app):
        """注册报告路由"""
        # 页面路由
        app.add_url_rule('/page/report', endpoint='page_report', view_func=login_required(self.page_report))
        # API路由
        app.add_url_rule('/report', endpoint='report', view_func=login_required(self.report), methods=['GET'])
        app.add_url_rule('/report_stream', endpoint='report_stream', view_func=login_required(self.report_stream), methods=['GET'])

    def page_report(self):
        """报告页面"""
        return render_template('report.html')

    def report(self):
        """生成今日日报"""
        result = self.service.get_report()

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('message'))

    def report_stream(self):
        """SSE流式生成日报"""
        def generate():
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def stream_result():
                    full_content = ""
                    async for chunk in self.service.generate_report_stream():
                        if chunk['type'] == 'thinking':
                            yield f"data: {json.dumps({'type': 'thinking', 'content': chunk['content']})}\n\n"
                        elif chunk['type'] == 'text':
                            full_content += chunk['content']
                        elif chunk['type'] == 'done':
                            from internal.pkg.utils import format_ai_response
                            report_html = format_ai_response(full_content)
                            yield f"data: {json.dumps({'type': 'done', 'content': report_html})}\n\n"
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                            return
                        elif chunk['type'] == 'error':
                            yield f"data: {json.dumps({'type': 'error', 'content': chunk['content']})}\n\n"

                gen = stream_result()
                try:
                    while True:
                        try:
                            chunk = loop.run_until_complete(gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    logger.error(f"流式生成日报异常: {e}")
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