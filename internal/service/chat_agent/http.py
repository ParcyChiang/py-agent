# internal/service/chat_agent/http.py
"""ChatAgent HTTP 处理器"""
import asyncio
import json
import logging
from typing import List, Optional, Dict
from flask import request, render_template, Response, session

from .service import ChatAgentService
from internal.pkg.response import success, error
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class ChatAgentHttp:
    """ChatAgent HTTP 处理器"""

    def __init__(self):
        self.service = ChatAgentService()

    def routes(self, app):
        """注册 ChatAgent 路由"""
        # 页面路由
        app.add_url_rule('/page/chat', endpoint='page_chat',
                         view_func=login_required(self.page_chat))

        # API 路由
        app.add_url_rule('/api/chat/sessions', endpoint='chat_sessions_list',
                         view_func=login_required(self.list_sessions), methods=['GET'])
        app.add_url_rule('/api/chat/sessions', endpoint='chat_sessions_create',
                         view_func=login_required(self.create_session), methods=['POST'])
        app.add_url_rule('/api/chat/sessions/<session_id>', endpoint='chat_sessions_delete',
                         view_func=login_required(self.delete_session), methods=['DELETE'])
        app.add_url_rule('/api/chat/history/<session_id>', endpoint='chat_history',
                         view_func=login_required(self.get_history), methods=['GET'])
        app.add_url_rule('/api/chat/send', endpoint='chat_send',
                         view_func=login_required(self.send_message), methods=['POST'])
        app.add_url_rule('/api/chat/confirm', endpoint='chat_confirm',
                         view_func=login_required(self.confirm_action), methods=['POST'])

    def page_chat(self):
        """ChatAgent 页面"""
        return render_template('chat.html')

    def list_sessions(self):
        """获取会话列表"""
        user_id = session.get('user_id')
        try:
            sessions = self.service.get_sessions(user_id)
            return success(data={'sessions': sessions})
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return error(f"获取失败: {str(e)}")

    def create_session(self):
        """创建会话"""
        user_id = session.get('user_id')
        username = session.get('username', '')
        data = request.get_json() or {}
        title = data.get('title', '')

        try:
            session_id = self.service.create_session(user_id, username, title)
            return success(data={'session_id': session_id, 'title': title or '新对话'})
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return error(f"创建失败: {str(e)}")

    def delete_session(self, session_id: str):
        """删除会话"""
        user_id = session.get('user_id')
        try:
            if self.service.delete_session(session_id, user_id):
                return success(message='会话已删除')
            return error('删除失败，会话不存在或无权删除')
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return error(f"删除失败: {str(e)}")

    def get_history(self, session_id: str):
        """获取会话历史"""
        user_id = session.get('user_id')
        try:
            messages = self.service.get_session_messages(session_id)
            return success(data={'session_id': session_id, 'messages': messages})
        except Exception as e:
            logger.error(f"获取会话历史失败: {e}")
            return error(f"获取失败: {str(e)}")

    def send_message(self):
        """发送消息"""
        user_id = session.get('user_id')
        username = session.get('username', '')
        data = request.get_json()

        session_id = data.get('session_id')
        message = data.get('message', '').strip()

        if not session_id:
            return error('session_id 不能为空')
        if not message:
            return error('消息不能为空')

        try:
            result, msg_order = asyncio.run(
                self.service.send_message(user_id, username, session_id, message)
            )
            return success(data=result)
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return error(f"处理失败: {str(e)}")

    def confirm_action(self):
        """确认操作"""
        user_id = session.get('user_id')
        username = session.get('username', '')
        data = request.get_json()

        session_id = data.get('session_id')
        step = data.get('step')  # 'intent' or 'diff'
        confirmed = data.get('confirmed', False)

        if not confirmed:
            return success(message='操作已取消')

        if not session_id or not step:
            return error('参数不完整')

        try:
            # 从上下文中获取 plan
            messages = self.service.get_session_messages(session_id)
            plan = self._extract_plan_from_messages(messages)

            if not plan:
                return error('无法找到待执行的操作')

            result = asyncio.run(
                self.service.confirm_action(user_id, username, session_id, step, plan)
            )
            return success(data=result)
        except Exception as e:
            logger.error(f"确认操作失败: {e}")
            return error(f"操作失败: {str(e)}")

    def _extract_plan_from_messages(self, messages: List[Dict]) -> Optional[Dict]:
        """从消息中提取最后一个 action_plan"""
        for msg in reversed(messages):
            if msg.get('role') == 'assistant' and msg.get('action_type') == 'mutation':
                try:
                    action_result = msg.get('action_result')
                    if action_result:
                        return json.loads(action_result)
                except:
                    pass
        return None
