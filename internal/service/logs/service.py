# pages/logs/service.py
"""日志页面服务层"""
from typing import List, Dict

from internal.pkg.dao import LogDAO


class LogService:
    """日志服务"""

    def __init__(self):
        self.log_dao = LogDAO()

    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """获取所有操作日志"""
        return self.log_dao.get_all_logs(limit)
