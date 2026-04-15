# internal/server/auth.py
"""认证业务逻辑层"""
from typing import Dict, Optional, Tuple

from internal.models.user import UserDAO
from internal.models.log import LogDAO


class AuthService:
    """认证业务服务"""

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

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        return self.user_dao.get_user_by_id(user_id)

    def get_all_users(self) -> list:
        """获取所有用户"""
        return self.user_dao.get_all_users()

    def delete_user(self, user_id: int, operator_id: int = None, operator_name: str = None, ip_address: str = None) -> Tuple[bool, str]:
        """删除用户"""
        success, message = self.user_dao.delete_user(user_id)

        if success and operator_id:
            self.log_dao.add_log(
                operator_id,
                operator_name or '',
                '删除用户',
                f'删除了用户ID={user_id}',
                ip_address or ''
            )

        return success, message

    def get_all_logs(self, limit: int = 100) -> list:
        """获取所有操作日志"""
        return self.log_dao.get_all_logs(limit)
