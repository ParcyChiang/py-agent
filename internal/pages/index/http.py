# pages/index/http.py
"""首页 HTTP 处理器"""
from flask import redirect, url_for, session


class IndexHttp:
    """首页 HTTP 处理器"""

    def index(self):
        """首页"""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        from flask import render_template
        return render_template('index.html')
