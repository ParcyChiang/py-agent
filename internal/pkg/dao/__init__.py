"""数据库初始化"""
import hashlib
import logging

import pymysql

from internal.configs.config import Config

# 重新导出 dao.py 中的类，保持向后兼容
from internal.pkg.dao.dao import ShipmentDAO, UserDAO, LogDAO, ChatHistoryDAO

logger = logging.getLogger("LogisticsAPI")

# 建表 SQL
CREATE_TABLES_SQL = [
    """CREATE TABLE IF NOT EXISTS shipments (
        id VARCHAR(128) PRIMARY KEY,
        origin VARCHAR(255),
        destination VARCHAR(255),
        origin_city VARCHAR(255),
        destination_city VARCHAR(255),
        status VARCHAR(64),
        estimated_delivery DATE,
        actual_delivery DATE,
        weight DOUBLE,
        dimensions TEXT,
        customer_id VARCHAR(128),
        courier_company VARCHAR(255),
        courier VARCHAR(255),
        package_type VARCHAR(128),
        priority VARCHAR(64),
        customer_type VARCHAR(128),
        payment_method VARCHAR(128),
        shipping_fee DOUBLE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS shipment_events (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        shipment_id VARCHAR(128),
        event_type VARCHAR(128),
        location VARCHAR(255),
        description TEXT,
        timestamp DATETIME,
        CONSTRAINT fk_shipment
            FOREIGN KEY (shipment_id) REFERENCES shipments(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        password VARCHAR(256) NOT NULL,
        role VARCHAR(32) DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS operation_logs (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        username VARCHAR(64),
        action VARCHAR(128),
        detail TEXT,
        ip_address VARCHAR(64),
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS chat_history (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        username VARCHAR(64) NOT NULL,
        page VARCHAR(64) NOT NULL COMMENT '页面标识：code_generator/analysis_report/compare等',
        title VARCHAR(256) DEFAULT '' COMMENT '对话标题/摘要',
        user_input TEXT NOT NULL COMMENT '用户输入',
        ai_response TEXT COMMENT 'AI响应内容',
        session_id VARCHAR(64) NOT NULL DEFAULT '' COMMENT '会话ID，关联同一轮对话',
        message_order INT NOT NULL DEFAULT 0 COMMENT '消息顺序',
        action_type VARCHAR(32) DEFAULT NULL COMMENT '动作类型：query/mutation/optimize/explain',
        action_result TEXT DEFAULT NULL COMMENT '执行结果（JSON）',
        diff_content TEXT DEFAULT NULL COMMENT '变更Diff（JSON）',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_page (user_id, page),
        INDEX idx_user_created (user_id, created_at),
        INDEX idx_session_id (session_id),
        INDEX idx_user_session (user_id, session_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
]


def _ensure_database():
    """确保数据库存在"""
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()


def _get_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=True,
    )


def _create_tables():
    """创建表结构"""
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            for sql in CREATE_TABLES_SQL:
                cursor.execute(sql)
        conn.commit()


def _init_admin_user():
    """初始化管理员账号"""
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
            if cursor.fetchone() is None:
                admin_password = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    ("admin", admin_password, "admin"),
                )
                logger.info("已创建默认管理员账号: admin / admin123")
        conn.commit()


def init_database():
    """初始化数据库（如果需要）"""
    _ensure_database()
    _create_tables()
    _init_admin_user()