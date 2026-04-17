# pages/users/service.py
"""用户管理页面服务层"""
from typing import List, Tuple, Dict

from internal.pages.users.dao import UserDAO, LogDAO


class AuthService:
    """用户管理服务"""

    def __init__(self):
        self.user_dao = UserDAO()
        self.log_dao = LogDAO()

    def get_all_users(self) -> List[Dict]:
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
