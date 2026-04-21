# internal/service/login/dao.py
"""用户和日志 DAO 层"""
import hashlib
import contextlib
from typing import Dict, List, Optional, Tuple

import pymysql
from pymysql.cursors import DictCursor

from internal.configs.config import Config


class UserDAO:
    """用户数据访问对象"""

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

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, role FROM users WHERE username = %s AND password = %s",
                    (username, self._hash_password(password))
                )
                user = cursor.fetchone()
                if user:
                    return True, user
                return False, None

    def create_user(self, username: str, password: str, role: str = "user") -> Tuple[bool, str]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if cursor.fetchone():
                        return False, "用户名已存在"
                    hashed_password = self._hash_password(password)
                    cursor.execute(
                        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                        (username, hashed_password, role)
                    )
                    conn.commit()
                    return True, "用户创建成功"
                except Exception as e:
                    conn.rollback()
                    return False, f"创建用户失败: {str(e)}"

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, role, created_at FROM users WHERE id = %s",
                    (user_id,)
                )
                return cursor.fetchone()

    def get_all_users(self) -> List[Dict]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
                return cursor.fetchall()

    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("DELETE FROM users WHERE id = %s AND role != 'admin'", (user_id,))
                    if cursor.rowcount == 0:
                        return False, "无法删除管理员账号"
                    conn.commit()
                    return True, "用户已删除"
                except Exception as e:
                    conn.rollback()
                    return False, f"删除失败: {str(e)}"


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

    def add_log(self, user_id: int, username: str, action: str, detail: str = "", ip_address: str = "") -> None:
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
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_id, username, action, detail, ip_address, timestamp FROM operation_logs ORDER BY timestamp DESC LIMIT %s",
                    (limit,)
                )
                return cursor.fetchall()

    def get_user_logs(self, user_id: int, limit: int = 50) -> List[Dict]:
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_id, username, action, detail, ip_address, timestamp FROM operation_logs WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s",
                    (user_id, limit)
                )
                return cursor.fetchall()