# middleware/logging.py
"""日志中间件"""
import logging
import time

from flask import request

logger = logging.getLogger("LogisticsAPI")


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )


def request_logging():
    """请求日志中间件"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time.time()

            logger.info(f"{request.method} {request.path} - Start")

            result = f(*args, **kwargs)

            elapsed = time.time() - start
            logger.info(f"{request.method} {request.path} - Completed in {elapsed:.3f}s")

            return result
        return wrapper
    return decorator


from functools import wraps
