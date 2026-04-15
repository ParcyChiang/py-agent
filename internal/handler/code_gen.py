# internal/handler/code_gen.py
"""代码生成 HTTP 处理器"""
import asyncio
from flask import request

from internal.server import CodeGenService
from internal.pkg.response import success, error


class CodeGenHandler:
    """代码生成 HTTP 处理器"""

    def __init__(self):
        self.service = CodeGenService()

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
