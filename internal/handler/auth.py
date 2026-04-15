# internal/handler/auth.py
"""认证 HTTP 处理器"""
from flask import request, session, redirect, url_for, render_template

from internal.server import AuthService
from internal.pkg.response import success, error


class AuthHandler:
    """认证 HTTP 处理器"""

    def __init__(self):
        self.service = AuthService()

    def login_page(self):
        """登录页面"""
        if request.method == 'POST':
            return self.login()
        return render_template('login.html')

    def login(self):
        """登录 API"""
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            if request.is_json:
                return error('请输入用户名和密码')
            return render_template('login.html', error='请输入用户名和密码')

        success_flag, user, message = self.service.login(username, password, request.remote_addr)

        if success_flag:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            if request.is_json:
                return success(
                    message='登录成功',
                    data={'username': user['username'], 'role': user['role']}
                )
            return redirect(url_for('index'))
        else:
            if request.is_json:
                return error(message)
            return render_template('login.html', error=message)

    def logout(self):
        """登出"""
        if 'user_id' in session:
            self.service.log_dao.add_log(
                session['user_id'],
                session['username'],
                '登出',
                '用户退出系统',
                request.remote_addr
            )
        session.clear()

        if request.is_json:
            return success(message='已登出')
        return redirect(url_for('login'))

    def api_logout(self):
        """API 登出"""
        session.clear()
        return success(message='已登出')

    def get_current_user(self):
        """获取当前用户"""
        if 'user_id' not in session:
            return error('未登录', 401)

        user = self.service.get_user_by_id(session['user_id'])
        if not user:
            return error('获取用户信息失败', 500)

        return success(data={'user': user})

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

    def api_login(self):
        """API 登录"""
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return error('请输入用户名和密码')

        success_flag, user, message = self.service.login(username, password, request.remote_addr)

        if success_flag:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return success(
                message='登录成功',
                data={'username': user['username'], 'role': user['role']}
            )
        else:
            return error(message)
