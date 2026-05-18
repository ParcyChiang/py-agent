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

    # 高德地图 API 配置
    AMAP_API_KEY = os.getenv("AMAP_API_KEY", "82de2ea63b894cfddb12e56f8e76a637")
    AMAP_GEO_KEY = os.getenv("AMAP_GEO_KEY", "2c35b15d80e3779d6db45ff9999cf3bb")

    # 地图物流数据配置
    MAP_SHIPMENT_LIMIT = int(os.getenv("MAP_SHIPMENT_LIMIT", "100"))


def get_config():
    """获取配置实例"""
    return Config
