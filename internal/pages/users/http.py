# pages/users/http.py
"""用户管理页面 HTTP 处理器"""
from flask import request, session

from internal.pages.users.service import AuthService
from internal.pkg.response import success, error


class UsersHttp:
    """用户管理页面 HTTP 处理器"""

    def __init__(self):
        self.service = AuthService()

    def get_users(self):
        """获取用户列表"""
        users = self.service.get_all_users()
        return success(data={'users': users})

    def delete_user(self, user_id):
        """删除用户"""
        success_flag, message = self.service.delete_user(
            user_id,
            operator_id=session.get('user_id'),
            operator_name=session.get('username'),
            ip_address=request.remote_addr
        )
        return {'success': success_flag, 'message': message}