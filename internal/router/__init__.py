# internal/router/__init__.py
"""路由注册"""
from flask import render_template, redirect, url_for, session, request

from internal.pages.login.http import LoginHttp
from internal.pages.register.http import RegisterHttp
from internal.pages.upload.http import UploadHttp
from internal.pages.analyze.http import AnalyzeHttp
from internal.pages.report.http import ReportHttp
from internal.pages.analysis_report.http import AnalysisReportHttp
from internal.pages.code_generator.http import CodeGeneratorHttp
from internal.pages.new_dashboard.http import NewDashboardHttp
from internal.pages.compare.http import CompareHttp
from internal.pages.logs.http import LogsHttp
from internal.pages.users.http import UsersHttp
from internal.pages.admin_log.http import AdminLogHttp
from internal.pages.index.http import IndexHttp
from internal.middleware import login_required, admin_required


def register_routes(app):
    """注册所有路由"""

    # 实例化处理器
    login_http = LoginHttp()
    register_http = RegisterHttp()
    upload_http = UploadHttp()
    analyze_http = AnalyzeHttp()
    report_http = ReportHttp()
    analysis_report_http = AnalysisReportHttp()
    code_gen_http = CodeGeneratorHttp()
    dashboard_http = NewDashboardHttp()
    compare_http = CompareHttp()
    logs_http = LogsHttp()
    users_http = UsersHttp()
    admin_log_http = AdminLogHttp()
    index_http = IndexHttp()

    # ==================== 页面路由 ====================

    @app.route('/')
    def index():
        return index_http.index()

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        return login_http.login_page()

    @app.route('/logout')
    def logout():
        return login_http.logout()

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        return register_http.register_page()

    @app.route('/page/logs')
    @login_required
    @admin_required
    def page_logs():
        return render_template('logs.html')

    @app.route('/page/users')
    @login_required
    @admin_required
    def page_users():
        return render_template('users.html')

    @app.route('/page/upload')
    @login_required
    def page_upload():
        return render_template('upload.html')

    @app.route('/page/analyze')
    @login_required
    def page_analyze():
        return render_template('analyze.html')

    @app.route('/page/report')
    @login_required
    def page_report():
        return render_template('report.html')

    @app.route('/page/code_generator')
    @login_required
    def page_code_generator():
        return render_template('code_generator.html')

    @app.route('/page/new_dashboard')
    @login_required
    def page_new_dashboard():
        return render_template('new_dashboard.html')

    @app.route('/page/compare')
    @login_required
    def page_compare():
        return render_template('compare.html')

    @app.route('/page/analysis_report')
    @login_required
    def page_analysis_report():
        return render_template('analysis_report.html')

    @app.route('/page/admin_log')
    @login_required
    @admin_required
    def page_admin_log():
        return render_template('admin_log.html')

    # ==================== API 路由 ====================

    # 认证 API
    @app.route('/api/login', methods=['POST'])
    def api_login():
        return login_http.api_login()

    @app.route('/api/logout', methods=['POST'])
    def api_logout():
        return login_http.api_logout()

    @app.route('/api/current_user')
    def api_current_user():
        return login_http.get_current_user()

    # 用户管理 API（需管理员权限）
    @app.route('/api/users')
    @login_required
    @admin_required
    def api_get_users():
        return users_http.get_users()

    @app.route('/api/users/<int:user_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def api_delete_user(user_id):
        return users_http.delete_user(user_id)

    # 日志 API（需管理员权限）
    @app.route('/api/logs')
    @login_required
    @admin_required
    def api_get_logs():
        return logs_http.get_logs()

    # 物流 API
    @app.route('/upload', methods=['POST'])
    @login_required
    def upload_file():
        return upload_http.upload()

    @app.route('/delete_csv', methods=['POST'])
    @login_required
    def delete_csv():
        return upload_http.delete_csv()

    @app.route('/shipments', methods=['GET'])
    def get_shipments():
        return upload_http.get_shipments()

    @app.route('/shipment/<shipment_id>', methods=['GET'])
    def get_shipment(shipment_id):
        return upload_http.get_shipment(shipment_id)

    @app.route('/analyze', methods=['GET'])
    @login_required
    def analyze_data():
        return analyze_http.analyze()

    @app.route('/report', methods=['GET'])
    @login_required
    def report_data():
        return report_http.report()

    @app.route('/analysis_report', methods=['GET'])
    @login_required
    def get_analysis_report():
        return analysis_report_http.get_analysis_report()

    @app.route('/chart_data', methods=['GET'])
    def get_chart_data():
        return analyze_http.get_chart_data()

    # 代码生成 API
    @app.route('/generate_code', methods=['POST'])
    async def generate_code():
        return await code_gen_http.generate_code()

    @app.route('/execute_code', methods=['POST'])
    def execute_code():
        return code_gen_http.execute_code()

    # 动态看板 API
    @app.route('/api/dashboard/trend', methods=['GET'])
    def get_dashboard_trend():
        return dashboard_http.get_trend()

    @app.route('/api/dashboard/metrics', methods=['GET'])
    def get_dashboard_metrics():
        return dashboard_http.get_metrics()

    @app.route('/api/dashboard/table', methods=['GET'])
    def get_dashboard_table():
        return dashboard_http.get_table()

    # 物流对比 API
    @app.route('/api/shipments/compare', methods=['GET'])
    @login_required
    def compare_shipments():
        return compare_http.get_compare_data()

    @app.route('/api/shipments/filters', methods=['GET'])
    @login_required
    def get_shipment_filters():
        return compare_http.get_filters()

    @app.route('/api/shipments/analyze-comparison', methods=['POST'])
    @login_required
    async def analyze_comparison():
        return await compare_http.analyze_comparison()