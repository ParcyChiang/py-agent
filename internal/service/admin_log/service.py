# pages/admin_log/service.py
"""管理员日志页面服务层"""
from typing import List, Dict

from internal.service.admin_log.dao import LogDAO


class LogService:
    """日志服务"""

    def __init__(self):
        self.log_dao = LogDAO()

    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """获取所有操作日志"""
        return self.log_dao.get_all_logs(limit)
