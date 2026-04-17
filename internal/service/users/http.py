# pages/users/http.py
"""用户管理页面 HTTP 处理器"""
from flask import request, session, render_template

from internal.service.users.service import AuthService
from internal.pkg.response import success, error
from internal.middleware import login_required, admin_required


class UsersHttp:
    """用户管理页面 HTTP 处理器"""

    def __init__(self):
        self.service = AuthService()

    def routes(self, app):
        """注册用户管理路由"""
        # 页面路由
        app.add_url_rule(
            '/page/users',
            endpoint='page_users',
            view_func=login_required(admin_required(self.page_users)),
        )
        # API路由
        app.add_url_rule(
            '/api/users',
            endpoint='api_users',
            view_func=login_required(admin_required(self.get_users)),
            methods=['GET']
        )
        app.add_url_rule(
            '/api/users/<int:user_id>',
            endpoint='api_delete_user',
            view_func=login_required(admin_required(self.delete_user)),
            methods=['DELETE']
        )

    def page_users(self):
        """用户管理页面"""
        return render_template('users.html')

    def get_users(self):
        """获取用户列表"""
        users = self.service.get_all_users()
        return success(data={'users': users})

    def delete_user(self, user_id):
        """删除用户"""
        success_flag, message = self.service.delete_user(
            user_id,
            operator_id=session.get('user_id'),
            operator_name=session.get('username'),
            ip_address=request.remote_addr
        )
        return {'success': success_flag, 'message': message}