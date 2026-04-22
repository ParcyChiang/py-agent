# internal/service/chat_agent/service.py
"""ChatAgent Service - Session 和消息管理"""
import json
import uuid
from typing import Dict, List, Optional, Tuple

from internal.pkg.dao import ChatHistoryDAO, ShipmentDAO
from internal.pkg.models.model_handler import AIModelHandler
from .agent import Agent


class ChatAgentService:
    """ChatAgent 服务"""

    MAX_CONTEXT_MESSAGES = 20  # 最多保留 20 条消息

    def __init__(self):
        self.chat_dao = ChatHistoryDAO()
        self.shipment_dao = ShipmentDAO()
        self.model = AIModelHandler()
        self.agent = Agent(self.shipment_dao, self.model)

    def create_session(self, user_id: int, username: str, title: str = "") -> str:
        """创建新会话"""
        if not title:
            title = f"新对话"
        return self.chat_dao.create_session(user_id, username, title)

    def get_sessions(self, user_id: int) -> List[Dict]:
        """获取用户的会话列表"""
        return self.chat_dao.get_user_sessions(user_id)

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """获取会话的所有消息"""
        messages = self.chat_dao.get_session_messages(session_id)
        # 限制上下文长度
        if len(messages) > self.MAX_CONTEXT_MESSAGES:
            messages = messages[-self.MAX_CONTEXT_MESSAGES:]
        return messages

    def delete_session(self, session_id: str, user_id: int) -> bool:
        """删除会话"""
        return self.chat_dao.delete_session(session_id, user_id)

    async def send_message(self, user_id: int, username: str,
                          session_id: str, message: str) -> Tuple[Dict, int]:
        """发送消息并处理"""
        # 获取上下文
        context = self.get_session_messages(session_id)

        # 处理消息
        response = await self.agent.process(message, context)

        # 保存用户消息
        user_msg_order = len(context) * 2 + 1
        self.chat_dao.add_message(
            user_id, username, session_id,
            user_msg_order, 'user', message
        )

        # 保存 AI 响应
        ai_msg_order = user_msg_order + 1
        self.chat_dao.add_message(
            user_id, username, session_id,
            ai_msg_order, 'assistant', response.content,
            action_type=response.type,
            action_result=response.action_result,
            diff_content=json.dumps(response.diff) if response.diff else None
        )

        return {
            'type': response.type,
            'content': response.content,
            'need_confirm': response.need_confirm,
            'action_plan': response.action_plan,
            'diff': response.diff,
            'error': response.error
        }, ai_msg_order

    async def confirm_action(self, user_id: int, username: str,
                            session_id: str, step: str, plan: Dict) -> Dict:
        """确认执行操作"""
        if step == 'intent':
            # 意图确认 → 返回 Diff
            result = await self.agent.execute_mutation(plan)
            # 更新最后一条 AI 消息的 diff
            return {
                'success': True,
                'need_diff_confirm': True,
                'diff': result.diff,
                'affected_rows': len(plan.get('affected_ids', [])),
                'content': result.content
            }
        elif step == 'diff':
            # Diff 确认 → 执行真正更新
            result = await self.agent.execute_mutation(plan)
            return {
                'success': True,
                'affected_rows': len(plan.get('affected_ids', [])),
                'message': result.content
            }
        else:
            return {
                'success': False,
                'message': f'未知的确认步骤: {step}'
            }
