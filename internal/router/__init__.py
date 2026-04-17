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

    # 注册各 page 模块的路由
    login_http.routes(app)
    register_http.routes(app)
    upload_http.routes(app)
    analyze_http.routes(app)
    report_http.routes(app)
    analysis_report_http.routes(app)
    code_gen_http.routes(app)
    dashboard_http.routes(app)
    compare_http.routes(app)
    logs_http.routes(app)
    users_http.routes(app)
    admin_log_http.routes(app)
    index_http.routes(app)