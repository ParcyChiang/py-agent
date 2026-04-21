# pages/analysis_report/http.py
"""分析报告页面 HTTP 处理器"""
import asyncio
import json
import logging
from flask import request, render_template, Response

from internal.service.analysis_report.service import AnalysisReportService
from internal.pkg.response import success, error
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class AnalysisReportHttp:
    """分析 HTTP 处理器"""

    def __init__(self):
        self.service = AnalysisReportService()

    def routes(self, app):
        """注册分析报告路由"""
        # 页面路由
        app.add_url_rule('/page/analysis_report', endpoint='page_analysis_report', view_func=login_required(self.page_analysis_report))
        # API路由
        app.add_url_rule('/analysis_stream', endpoint='analysis_stream', view_func=login_required(self.analysis_stream), methods=['GET'])

    def page_analysis_report(self):
        """分析报告页面"""
        return render_template('analysis_report.html')

    def analysis_stream(self):
        """SSE流式生成AI分析报告"""
        def generate():
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def stream_result():
                    async for item in self.service.generate_analysis_stream_with_format():
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
                try:
                    while True:
                        try:
                            chunk = loop.run_until_complete(gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    logger.error(f"流式生成AI分析报告异常: {e}")
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
