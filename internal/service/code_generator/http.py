# pages/code_generator/http.py
"""代码生成页面 HTTP 处理器"""
import asyncio
import time
import json
import logging
from flask import request, render_template, Response, session

from internal.service.code_generator.service import CodeGenService
from internal.pkg.response import success, error
from internal.pkg.dao import ChatHistoryDAO
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class CodeGeneratorHttp:
    """代码生成 HTTP 处理器"""

    def __init__(self):
        self.service = CodeGenService()
        self.chat_dao = ChatHistoryDAO()

    def routes(self, app):
        """注册代码生成路由"""
        # 页面路由
        app.add_url_rule('/page/code_generator', endpoint='page_code_generator', view_func=login_required(self.page_code_generator))
        # API路由
        app.add_url_rule('/generate_code_stream', endpoint='generate_code_stream', view_func=login_required(self.generate_code_stream), methods=['POST'])
        app.add_url_rule('/execute_code', endpoint='execute_code', view_func=login_required(self.execute_code), methods=['POST'])

    def page_code_generator(self):
        """代码生成页面"""
        return render_template('code_generator.html')

    def generate_code_stream(self):
        """SSE流式生成代码，实时发送thinking让前端显示"""
        # 在请求上下文内提前获取 session 值
        user_id = session.get('user_id') or 0
        username = session.get('username', '游客')

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
                            # 处理 code 格式
                            code = full_code
                            if code.startswith('```python'):
                                code = code[9:]
                            if code.startswith('```'):
                                code = code[3:]
                            if code.endswith('```'):
                                code = code[:-3]
                            code = code.strip()

                            yield f"data: {json.dumps({'type': 'done', 'code': code})}\n\n"
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                            return
                        elif chunk['type'] == 'error':
                            yield f"data: {json.dumps({'type': 'error', 'content': chunk['content']})}\n\n"

                # 运行异步生成器
                gen = stream_result()
                done_code = None
                try:
                    while True:
                        try:
                            chunk = loop.run_until_complete(gen.__anext__())
                            # 捕获 done 类型的 code 用于后续入库
                            if done_code is None and 'done' in chunk:
                                try:
                                    data = json.loads(chunk.split('data: ')[1].split('\n')[0])
                                    if data.get('type') == 'done':
                                        done_code = data.get('code', '')
                                except:
                                    pass
                            yield chunk
                        except StopAsyncIteration:
                            break
                except Exception as e:
                    logger.error(f"流式生成异常: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

                # 流结束后，保存到对话历史
                if done_code:
                    try:
                        self.chat_dao.create_chat(
                            user_id=user_id,
                            username=username,
                            page='code_generator',
                            title='代码生成 - ' + question[:50],
                            user_input=question,
                            ai_response=done_code
                        )
                        logger.info(f"代码生成已自动保存到对话历史, user_id={user_id}")
                    except Exception as e:
                        logger.error(f"保存代码生成到对话历史失败: {e}")
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
