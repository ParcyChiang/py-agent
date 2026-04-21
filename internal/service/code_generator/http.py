# pages/code_generator/http.py
"""代码生成页面 HTTP 处理器"""
import asyncio
import time
import json
import logging
from flask import request, render_template, Response

from internal.service.code_generator.service import CodeGenService
from internal.pkg.response import success, error
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class CodeGeneratorHttp:
    """代码生成 HTTP 处理器"""

    def __init__(self):
        self.service = CodeGenService()

    def routes(self, app):
        """注册代码生成路由"""
        # 页面路由
        app.add_url_rule('/page/code_generator', endpoint='page_code_generator', view_func=login_required(self.page_code_generator))
        # API路由
        app.add_url_rule('/generate_code', endpoint='generate_code', view_func=login_required(self.generate_code), methods=['POST'])
        app.add_url_rule('/generate_code_stream', endpoint='generate_code_stream', view_func=login_required(self.generate_code_stream), methods=['POST'])
        app.add_url_rule('/execute_code', endpoint='execute_code', view_func=login_required(self.execute_code), methods=['POST'])

    def page_code_generator(self):
        """代码生成页面"""
        return render_template('code_generator.html')

    async def generate_code(self):
        """生成代码"""
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return error('请输入问题')

        result = await self.service.generate_code(question)

        if result.get('success'):
            return success(data={'code': result.get('code'), 'thinking': result.get('thinking', '')})
        else:
            return error(result.get('message'))

    def generate_code_stream(self):
        """SSE流式生成代码，实时发送thinking让前端显示"""
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return error('请输入问题')

        def generate():
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            # 使用异步生成器流式获取结果
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                async def stream_result():
                    full_code = ""  # 累积完整 code
                    async for chunk in self.service.generate_code_stream(question):
                        if chunk['type'] == 'thinking':
                            yield f"data: {json.dumps({'type': 'thinking', 'content': chunk['content']})}\n\n"
                        elif chunk['type'] == 'text':
                            full_code += chunk['content']
                        elif chunk['type'] == 'done':
                            yield f"data: {json.dumps({'type': 'done', 'code': chunk['code']})}\n\n"
                        elif chunk['type'] == 'error':
                            yield f"data: {json.dumps({'type': 'error', 'content': chunk['content']})}\n\n"

                    # 流结束后，发送累积的完整 code
                    yield f"data: {json.dumps({'type': 'done', 'code': full_code})}\n\n"
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"

                # 运行异步生成器
                gen = stream_result()
                try:
                    while True:
                        try:
                            chunk = loop.run_until_complete(gen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    logger.error(f"流式生成异常: {e}")
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

    def execute_code(self):
        """执行代码"""
        data = request.get_json()
        code = data.get('code', '').strip()

        result = self.service.execute_code(code)

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('error'))
