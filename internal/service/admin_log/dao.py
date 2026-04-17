# pages/admin_log/dao.py
"""管理员日志页面 DAO 层"""
import contextlib
from typing import Dict, List

import pymysql
from pymysql.cursors import DictCursor

from internal.configs.config import Config


class LogDAO:
    """操作日志数据访问对象"""

    def __init__(self):
        self.host = Config.MYSQL_HOST
        self.port = Config.MYSQL_PORT
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD
        self.database = Config.MYSQL_DATABASE

    def _get_connection(self, with_db: bool = True):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database if with_db else None,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )

    @contextlib.contextmanager
    def get_connection(self, with_db: bool = True):
        conn = self._get_connection(with_db)
        try:
            yield conn
        finally:
            conn.close()

    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_id, username, action, detail, ip_address, timestamp FROM operation_logs ORDER BY timestamp DESC LIMIT %s",
                    (limit,)
                )
                return cursor.fetchall()
