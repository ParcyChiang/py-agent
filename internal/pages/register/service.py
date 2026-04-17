# pages/register/service.py
"""注册页面服务层"""
from typing import Tuple

from internal.pages.register.dao import UserDAO, LogDAO


class AuthService:
    """认证服务"""

    def __init__(self):
        self.user_dao = UserDAO()
        self.log_dao = LogDAO()

    def register(self, username: str, password: str, ip_address: str = None) -> Tuple[bool, str]:
        """用户注册"""
        success, message = self.user_dao.create_user(username, password)

        if success:
            self.log_dao.add_log(
                0,
                username,
                '注册',
                '用户注册新账号',
                ip_address or ''
            )

        return success, message
