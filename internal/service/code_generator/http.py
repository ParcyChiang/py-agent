# pages/code_generator/http.py
"""代码生成页面 HTTP 处理器"""
import asyncio
from flask import request, render_template

from internal.service.code_generator.service import CodeGenService
from internal.pkg.response import success, error
from internal.middleware import login_required


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
            return success(data={'code': result.get('code')})
        else:
            return error(result.get('message'))

    def execute_code(self):
        """执行代码"""
        data = request.get_json()
        code = data.get('code', '').strip()

        result = self.service.execute_code(code)

        if result.get('success'):
            return success(data=result)
        else:
            return error(result.get('error'))
