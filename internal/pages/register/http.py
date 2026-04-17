# pages/register/http.py
"""注册页面 HTTP 处理器"""
from flask import request, session, redirect, url_for, render_template

from internal.pages.register.service import AuthService
from internal.pkg.response import success, error


class RegisterHttp:
    """认证 HTTP 处理器"""

    def __init__(self):
        self.service = AuthService()

    def routes(self, app):
        """注册注册路由"""
        app.add_url_rule('/register', endpoint='register', view_func=self.register_page, methods=['GET', 'POST'])

    def register_page(self):
        """注册页面"""
        if request.method == 'POST':
            return self.register()
        return render_template('register.html')

    def register(self):
        """注册"""
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password:
            return render_template('register.html', error='请输入用户名和密码')

        if len(username) < 3:
            return render_template('register.html', error='用户名至少3个字符')

        if len(password) < 6:
            return render_template('register.html', error='密码至少6个字符')

        if password != confirm_password:
            return render_template('register.html', error='两次密码输入不一致')

        success_flag, message = self.service.register(username, password, request.remote_addr)

        if success_flag:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error=message)