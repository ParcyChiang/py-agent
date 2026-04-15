# models/log.py
"""操作日志数据访问层"""
import contextlib
from typing import Dict, List

import pymysql
from pymysql.cursors import DictCursor

from internal.pkg.config import Config


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
        """数据库连接上下文管理器"""
        conn = self._get_connection(with_db)
        try:
            yield conn
        finally:
            conn.close()

    def add_log(self, user_id: int, username: str, action: str, detail: str = "", ip_address: str = "") -> None:
        """添加操作日志"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(
                        "INSERT INTO operation_logs (user_id, username, action, detail, ip_address) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, username, action, detail, ip_address)
                    )
                    conn.commit()
                except Exception as e:
                    print(f"添加日志失败: {e}")

    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """获取所有操作日志"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_id, username, action, detail, ip_address, timestamp FROM operation_logs ORDER BY timestamp DESC LIMIT %s",
                    (limit,)
                )
                return cursor.fetchall()

    def get_user_logs(self, user_id: int, limit: int = 50) -> List[Dict]:
        """获取指定用户的操作日志"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_id, username, action, detail, ip_address, timestamp FROM operation_logs WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
                    (user_id, limit)
                )
                return cursor.fetchall()
