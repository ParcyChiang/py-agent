"""Flask 应用入口"""
import os
import logging

from flask import Flask

from internal.pkg.config import Config
from internal.middleware.logging import setup_logging
from internal.router import register_routes

# 设置日志
setup_logging()
logger = logging.getLogger("LogisticsAPI")

# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH


def init_database():
    """初始化数据库（如果需要）"""
    from internal.pages.upload.dao import ShipmentDAO
    import pymysql
    import contextlib

    # 确保数据库存在
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
                f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DATABASE}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conn.close()

    # 初始化表结构
    shipment_dao = ShipmentDAO()
    with shipment_dao.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shipments (
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
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shipment_events (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    shipment_id VARCHAR(128),
                    event_type VARCHAR(128),
                    location VARCHAR(255),
                    description TEXT,
                    timestamp DATETIME,
                    CONSTRAINT fk_shipment
                        FOREIGN KEY (shipment_id) REFERENCES shipments(id)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    password VARCHAR(256) NOT NULL,
                    role VARCHAR(32) DEFAULT 'user',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    username VARCHAR(64),
                    action VARCHAR(128),
                    detail TEXT,
                    ip_address VARCHAR(64),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            # 初始化管理员账号
            import hashlib
            cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
            if cursor.fetchone() is None:
                admin_password = hashlib.sha256("admin123".encode()).hexdigest()
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    ("admin", admin_password, "admin")
                )
                logger.info("已创建默认管理员账号: admin / admin123")

        conn.commit()


# 注册路由
register_routes(app)

# 初始化数据库
init_database()


if __name__ == '__main__':
    logger.info("启动物流管理系统...")
    app.run(debug=True, host='0.0.0.0', port=5000)
