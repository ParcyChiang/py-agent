"""统一响应结构"""
from flask import jsonify


def success(data=None, message=None):
    """成功响应"""
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response.update(data)
    return jsonify(response)


def error(message, code=400):
    """错误响应"""
    return jsonify({
        'success': False,
        'message': message
    }), code


def api_success(success_flag=True, message=None, **kwargs):
    """API 成功响应（兼容现有格式）"""
    response = {'success': success_flag}
    if message:
        response['message'] = message
    response.update(kwargs)
    return jsonify(response)


def api_error(message, code=400):
    """API 错误响应"""
    return jsonify({
        'success': False,
        'message': message
    }), code
