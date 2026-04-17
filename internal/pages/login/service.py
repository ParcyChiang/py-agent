# pages/login/service.py
"""登录页面服务层"""
from typing import Dict, Optional, Tuple

from internal.pages.login.dao import UserDAO, LogDAO


class AuthService:
    """认证服务"""

    def __init__(self):
        self.user_dao = UserDAO()
        self.log_dao = LogDAO()

    def login(self, username: str, password: str, ip_address: str = None) -> Tuple[bool, Optional[Dict], str]:
        """用户登录"""
        success, user = self.user_dao.verify_user(username, password)

        if success:
            self.log_dao.add_log(
                user['id'],
                user['username'],
                '登录',
                '用户登录系统',
                ip_address or ''
            )
            return True, user, '登录成功'
        else:
            return False, None, '用户名或密码错误'

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        return self.user_dao.get_user_by_id(user_id)

    def add_log(self, user_id: int, username: str, action: str, detail: str = "", ip_address: str = "") -> None:
        """添加操作日志"""
        self.log_dao.add_log(user_id, username, action, detail, ip_address)
