"""Flask 应用入口"""
import os
import logging

from flask import Flask

from internal.configs.config import Config
from internal.middleware.logging import setup_logging
from internal.service.service import register_routes
from internal.pkg.dao import init_database

# 设置日志
setup_logging()
logger = logging.getLogger("LogisticsAPI")

# 创建 Flask 应用
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'), static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# 注册路由
register_routes(app)

# 初始化数据库
init_database()


if __name__ == '__main__':
    logger.info("启动物流管理系统...")
    app.run(debug=True, host='0.0.0.0', port=5000)
