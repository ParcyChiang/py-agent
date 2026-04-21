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
        app.add_url_rule('/analysis_report', endpoint='get_analysis_report', view_func=login_required(self.get_analysis_report), methods=['GET'])
        app.add_url_rule('/analysis_report_stream', endpoint='analysis_report_stream', view_func=login_required(self.analysis_report_stream), methods=['GET'])

    def page_analysis_report(self):
        """分析报告页面"""
        return render_template('analysis_report.html')

    def get_analysis_report(self):
        """生成运营分析报告"""
        result = self.service.get_analysis_report()

        if result.get('success'):
            return success(data={
                'analysis': result.get('analysis'),
                'daily_report': result.get('daily_report')
            })
        else:
            return error(result.get('message'))

    def analysis_report_stream(self):
        """SSE流式生成分析报告"""
        def generate():
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def stream_result():
                    analysis_content = ""
                    report_content = ""
                    current_report = None

                    async for chunk in self.service.generate_analysis_report_stream():
                        if chunk['type'] == 'report_type':
                            current_report = chunk['content']
                            yield f"data: {json.dumps({'type': 'report_start', 'content': current_report})}\n\n"
                        elif chunk['type'] == 'thinking':
                            yield f"data: {json.dumps({'type': 'thinking', 'content': chunk['content'], 'report': current_report})}\n\n"
                        elif chunk['type'] == 'text':
                            if current_report == 'analysis':
                                analysis_content += chunk['content']
                            else:
                                report_content += chunk['content']
                            yield f"data: {json.dumps({'type': 'text', 'content': chunk['content'], 'report': current_report})}\n\n"
                        elif chunk['type'] == 'done':
                            from internal.pkg.utils import format_ai_response
                            analysis_html = format_ai_response(analysis_content)
                            report_html = format_ai_response(report_content)
                            yield f"data: {json.dumps({'type': 'done', 'analysis': analysis_html, 'daily_report': report_html})}\n\n"
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
                    logger.error(f"流式生成分析报告异常: {e}")
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
