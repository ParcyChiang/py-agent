# internal/service/chat_history/http.py
"""对话历史 HTTP 处理器"""
import logging
from flask import request, session

from internal.pkg.dao import ChatHistoryDAO
from internal.pkg.response import success, error
from internal.middleware import login_required

logger = logging.getLogger("LogisticsAgent")


class ChatHistoryHttp:
    """对话历史 HTTP 处理器"""

    def __init__(self):
        self.dao = ChatHistoryDAO()

    def routes(self, app):
        """注册对话历史路由"""
        app.add_url_rule('/api/chat_history/create', endpoint='chat_history_create',
                         view_func=login_required(self.create_chat), methods=['POST'])
        app.add_url_rule('/api/chat_history/list', endpoint='chat_history_list',
                         view_func=login_required(self.list_chats), methods=['GET'])
        app.add_url_rule('/api/chat_history/get/<int:chat_id>', endpoint='chat_history_get',
                         view_func=login_required(self.get_chat), methods=['GET'])
        app.add_url_rule('/api/chat_history/delete/<int:chat_id>', endpoint='chat_history_delete',
                         view_func=login_required(self.delete_chat), methods=['DELETE'])
        app.add_url_rule('/api/chat_history/search', endpoint='chat_history_search',
                         view_func=login_required(self.search_chats), methods=['GET'])

    def create_chat(self):
        """创建对话记录"""
        data = request.get_json()
        page = data.get('page', '')
        title = data.get('title', '')
        user_input = data.get('user_input', '')
        ai_response = data.get('ai_response', '')

        if not page or not user_input:
            return error('page和user_input不能为空')

        user_id = session.get('user_id')
        username = session.get('username', '')

        try:
            chat_id = self.dao.create_chat(user_id, username, page, title, user_input, ai_response)
            return success(data={'id': chat_id})
        except Exception as e:
            logger.error(f"创建对话记录失败: {e}")
            return error(f"创建失败: {str(e)}")

    def list_chats(self):
        """获取对话列表"""
        page = request.args.get('page', '')
        limit = int(request.args.get('limit', 50))
        user_id = session.get('user_id')

        try:
            chats = self.dao.get_user_chats(user_id, page if page else None, limit)
            return success(data={'chats': chats})
        except Exception as e:
            logger.error(f"获取对话列表失败: {e}")
            return error(f"获取失败: {str(e)}")

    def get_chat(self, chat_id: int):
        """获取单条对话"""
        user_id = session.get('user_id')

        try:
            chat = self.dao.get_chat_by_id(chat_id)
            if not chat:
                return error('对话不存在')
            return success(data={'chat': chat})
        except Exception as e:
            logger.error(f"获取对话失败: {e}")
            return error(f"获取失败: {str(e)}")

    def delete_chat(self, chat_id: int):
        """删除对话"""
        user_id = session.get('user_id')

        try:
            if self.dao.delete_chat(chat_id, user_id):
                return success(message='删除成功')
            return error('删除失败，对话不存在或无权删除')
        except Exception as e:
            logger.error(f"删除对话失败: {e}")
            return error(f"删除失败: {str(e)}")

    def search_chats(self):
        """搜索对话"""
        keyword = request.args.get('keyword', '')
        limit = int(request.args.get('limit', 20))
        user_id = session.get('user_id')

        if not keyword:
            return error('keyword不能为空')

        try:
            chats = self.dao.search_chats(user_id, keyword, limit)
            return success(data={'chats': chats})
        except Exception as e:
            logger.error(f"搜索对话失败: {e}")
            return error(f"搜索失败: {str(e)}")
