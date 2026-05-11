# internal/service/chat_agent/handlers/explain.py
"""纯对话 Handler"""
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class ExplainHandler(BaseHandler):
    """Explain Handler - 处理无需执行操作的对话"""

    SYSTEM_PROMPT = """你是一个智能物流助手。用户只是想了解概念或闲聊，不需要执行任何数据库操作。

请用友好、专业的方式回答用户的问题。"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理对话请求"""
        user_message = intent.get('message', '')

        try:
            # 构建对话上下文
            history = self._build_messages(context, user_message)
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{history}"

            # 调用 AI 生成回复
            response_text = ""
            async for chunk in self.model.generate_response_stream(full_prompt, ""):
                if chunk['type'] == 'text':
                    response_text += chunk['content']

            return HandlerResponse(
                type='explain',
                content=response_text or '抱歉，我无法生成回复',
                need_confirm=False
            )
        except Exception as e:
            return HandlerResponse(
                type='explain',
                content=f'抱歉，处理您的请求时出现错误: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    async def handle_stream(self, intent: Dict, context: List[Dict]):
        """流式处理对话请求"""
        user_message = intent.get('message', '')

        try:
            # 构建对话上下文
            history = self._build_messages(context, user_message)
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{history}"

            # 流式调用 AI 生成回复
            async for chunk in self.model.generate_response_stream(full_prompt, ""):
                yield chunk

        except Exception as e:
            yield {'type': 'error', 'content': f'处理您的请求时出现错误: {str(e)}'}

    def _build_messages(self, context: List[Dict], current_message: str) -> str:
        """构建对话历史上下文"""
        history = ""
        for msg in context[-10:]:  # 最近 10 条消息
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'user':
                history += f"用户：{content}\n"
            else:
                history += f"助手：{content}\n"
        history += f"用户：{current_message}\n"
        return history
