# internal/router/__init__.py
"""路由注册"""
from flask import render_template, redirect, url_for, session, request

from internal.handler import (
    ShipmentHandler, AuthHandler, AnalysisHandler,
    DashboardHandler, CodeGenHandler
)
from internal.middleware import login_required, admin_required


def register_routes(app):
    """注册所有路由"""

    # 实例化处理器
    auth_handler = AuthHandler()
    shipment_handler = ShipmentHandler()
    analysis_handler = AnalysisHandler()
    dashboard_handler = DashboardHandler()
    code_gen_handler = CodeGenHandler()

    # ==================== 页面路由 ====================

    @app.route('/')
    def index():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        return auth_handler.login_page()

    @app.route('/logout')
    def logout():
        return auth_handler.logout()

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        return auth_handler.register_page()

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

    # ==================== API 路由 ====================

    # 认证 API
    @app.route('/api/login', methods=['POST'])
    def api_login():
        return auth_handler.api_login()

    @app.route('/api/logout', methods=['POST'])
    def api_logout():
        return auth_handler.api_logout()

    @app.route('/api/current_user')
    def api_current_user():
        return auth_handler.get_current_user()

    # 用户管理 API（需管理员权限）
    @app.route('/api/users')
    @login_required
    @admin_required
    def api_get_users():
        from internal.server import AuthService
        service = AuthService()
        users = service.get_all_users()
        return {'success': True, 'users': users}

    @app.route('/api/users/<int:user_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def api_delete_user(user_id):
        from internal.server import AuthService
        service = AuthService()
        success, message = service.delete_user(
            user_id,
            operator_id=session.get('user_id'),
            operator_name=session.get('username'),
            ip_address=request.remote_addr
        )
        return {'success': success, 'message': message}

    # 日志 API（需管理员权限）
    @app.route('/api/logs')
    @login_required
    @admin_required
    def api_get_logs():
        limit = request.args.get('limit', 100, type=int)
        from internal.server import AuthService
        service = AuthService()
        logs = service.get_all_logs(limit)
        return {'success': True, 'logs': logs}

    # 物流 API
    @app.route('/upload', methods=['POST'])
    @login_required
    def upload_file():
        return shipment_handler.upload()

    @app.route('/delete_csv', methods=['POST'])
    @login_required
    def delete_csv():
        return shipment_handler.delete_csv()

    @app.route('/shipments', methods=['GET'])
    def get_shipments():
        return shipment_handler.get_shipments()

    @app.route('/shipment/<shipment_id>', methods=['GET'])
    def get_shipment(shipment_id):
        return shipment_handler.get_shipment(shipment_id)

    # 分析 API
    @app.route('/analyze', methods=['GET'])
    @login_required
    def analyze_data():
        return analysis_handler.analyze()

    @app.route('/analysis_report', methods=['GET'])
    @login_required
    def get_analysis_report():
        return analysis_handler.get_analysis_report()

    @app.route('/chart_data', methods=['GET'])
    def get_chart_data():
        return analysis_handler.get_chart_data()

    # 代码生成 API
    @app.route('/generate_code', methods=['POST'])
    async def generate_code():
        return await code_gen_handler.generate_code()

    @app.route('/execute_code', methods=['POST'])
    def execute_code():
        return code_gen_handler.execute_code()

    # 动态看板 API
    @app.route('/api/dashboard/trend', methods=['GET'])
    def get_dashboard_trend():
        return dashboard_handler.get_trend()

    @app.route('/api/dashboard/metrics', methods=['GET'])
    def get_dashboard_metrics():
        return dashboard_handler.get_metrics()

    @app.route('/api/dashboard/table', methods=['GET'])
    def get_dashboard_table():
        return dashboard_handler.get_table()

    # 物流对比 API
    @app.route('/api/shipments/compare', methods=['GET'])
    @login_required
    def compare_shipments():
        return _compare_shipments()

    @app.route('/api/shipments/filters', methods=['GET'])
    @login_required
    def get_shipment_filters():
        return _get_shipment_filters()

    @app.route('/api/shipments/analyze-comparison', methods=['POST'])
    @login_required
    async def analyze_comparison():
        return await _analyze_comparison()


# ==================== 辅助函数 ====================

def _compare_shipments():
    """对比同一收件地址或发件地址的物流信息"""
    from internal.server import ShipmentService
    from datetime import datetime

    origin_filter = request.args.get('origin', '')
    destination_filter = request.args.get('destination', '')
    courier_filter = request.args.get('courier', '')
    page = request.args.get('page', 1, type=int)
    pageSize = request.args.get('pageSize', 20, type=int)

    service = ShipmentService()
    shipments, _ = service.get_shipments(limit=10000)

    if not shipments:
        return {'success': False, 'message': '没有可用的数据'}

    # 过滤
    filtered_shipments = []
    for shipment in shipments:
        origin = shipment.get('origin', '')
        destination = shipment.get('destination', '')
        courier = shipment.get('courier_company', '')

        if origin_filter and origin_filter not in origin:
            continue
        if destination_filter and destination_filter not in destination:
            continue
        if courier_filter and courier_filter not in courier:
            continue

        filtered_shipments.append(shipment)

    # 按地址分组
    address_groups = {}
    for shipment in filtered_shipments:
        destination = shipment.get('destination', '')
        if destination:
            if destination not in address_groups:
                address_groups[destination] = {'type': 'destination', 'shipments': []}
            address_groups[destination]['shipments'].append(shipment)

        origin = shipment.get('origin', '')
        if origin:
            if origin not in address_groups:
                address_groups[origin] = {'type': 'origin', 'shipments': []}
            address_groups[origin]['shipments'].append(shipment)

    # 过滤出有两条以上记录的地址
    valid_groups = {}
    for address, group in address_groups.items():
        if len(group['shipments']) >= 2:
            valid_groups[address] = group

    # 分析
    comparison_results = []
    for address, group in valid_groups.items():
        shipments_list = group['shipments']

        delivery_times = []
        for shipment in shipments_list:
            if shipment.get('actual_delivery') and shipment.get('created_at'):
                try:
                    created = datetime.fromisoformat(str(shipment['created_at']).replace('Z', '+00:00'))
                    delivered = datetime.fromisoformat(str(shipment['actual_delivery']).replace('Z', '+00:00'))
                    hours = (delivered - created).total_seconds() / 3600
                    delivery_times.append(hours)
                except:
                    pass

        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0

        status_counts = {}
        for shipment in shipments_list:
            status = shipment.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        courier_counts = {}
        for shipment in shipments_list:
            courier = shipment.get('courier_company', 'unknown')
            courier_counts[courier] = courier_counts.get(courier, 0) + 1

        total_fee = sum(shipment.get('shipping_fee', 0) for shipment in shipments_list)
        avg_fee = total_fee / len(shipments_list) if shipments_list else 0

        comparison_results.append({
            'address': address,
            'address_type': group['type'],
            'shipment_count': len(shipments_list),
            'avg_delivery_time': avg_delivery_time,
            'status_distribution': status_counts,
            'courier_distribution': courier_counts,
            'avg_shipping_fee': avg_fee,
            'shipments': shipments_list
        })

    comparison_results.sort(key=lambda x: x['shipment_count'], reverse=True)

    total = len(comparison_results)
    start = (page - 1) * pageSize
    end = start + pageSize
    page_data = comparison_results[start:end]

    return {
        'success': True,
        'data': page_data,
        'total': total,
        'page': page,
        'pageSize': pageSize
    }


def _get_shipment_filters():
    """获取物流筛选过滤选项"""
    from internal.server import ShipmentService

    service = ShipmentService()
    shipments, _ = service.get_shipments(limit=10000)

    origins = sorted(list(set(s.get('origin', '') for s in shipments if s.get('origin'))))
    destinations = sorted(list(set(s.get('destination', '') for s in shipments if s.get('destination'))))
    couriers = sorted(list(set(s.get('courier_company', '') for s in shipments if s.get('courier_company'))))

    return {
        'success': True,
        'origins': origins,
        'destinations': destinations,
        'couriers': couriers
    }


async def _analyze_comparison():
    """使用LLM分析物流对比数据"""
    from internal.server import CodeGenService

    data = request.get_json()
    comparison_data = data.get('comparison_data', [])

    if not comparison_data:
        return {'success': False, 'message': '没有提供对比数据'}

    prompt = f"""
    你是一个物流运营专家，需要对以下物流对比数据进行分析并给出优化方案：

    {comparison_data}

    请按照以下结构输出分析结果：
    1. 数据概览：总结对比情况
    2. 关键发现：识别出的问题和异常情况
    3. 优化方案：针对发现的问题给出具体的优化建议
    4. 实施优先级：对优化方案进行优先级排序

    分析要具体、可操作，基于实际物流运营场景。
    """

    service = CodeGenService()
    analysis = await service.model_handler.generate_response(prompt)

    return {
        'success': True,
        'analysis': analysis
    }
