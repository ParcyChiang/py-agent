"""配置模块 - 集中管理应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置"""

    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # MySQL 数据库配置
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootroot")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "logistics")

    # MiniMax API 配置
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
    MINIMAX_API_URL = os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/anthropic/v1/messages")
    MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7-highspeed")


def get_config():
    """获取配置实例"""
    return Config
