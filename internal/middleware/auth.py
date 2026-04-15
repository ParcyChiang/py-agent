# middleware/auth.py
"""认证中间件"""
import asyncio
from functools import wraps
from flask import session, jsonify, redirect, url_for

from internal.pkg.response import error


def login_required(f):
    """登录检查装饰器（支持同步和异步函数）"""
    @wraps(f)
    async def decorated_async_function(*args, **kwargs):
        if 'user_id' not in session:
            if request_wants_json():
                return jsonify({'success': False, 'message': '未登录'})
            return redirect(url_for('login'))
        return await f(*args, **kwargs)

    @wraps(f)
    def decorated_sync_function(*args, **kwargs):
        if 'user_id' not in session:
            if request_wants_json():
                return jsonify({'success': False, 'message': '未登录'})
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    if asyncio.iscoroutinefunction(f):
        return decorated_async_function
    return decorated_sync_function


def admin_required(f):
    """管理员权限检查装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return error('未登录', 401)
        if session.get('role') != 'admin':
            return error('无权限', 403)
        return f(*args, **kwargs)
    return decorated_function


def request_wants_json():
    """判断请求是否期望 JSON 响应"""
    from flask import request
    return request.headers.get('Accept') == 'application/json' or request.is_json
