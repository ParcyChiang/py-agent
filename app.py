import os
import asyncio
import uuid
import atexit
import signal
import sys
import io
import contextlib
import traceback
from flask import Flask, render_template, request, jsonify

# 直接从models模块导入创建函数和类
from models import create_data_manager, create_model_handler
from utils import format_ai_response
from collections import Counter, defaultdict
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

# 使用工厂函数创建实例
data_manager = create_data_manager()
model_handler = create_model_handler()


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/page/upload')
def page_upload():
    return render_template('upload.html')

@app.route('/page/analyze')
def page_analyze():
    return render_template('analyze.html')

@app.route('/page/shipments')
def page_shipments():
    return render_template('shipments.html')

@app.route('/page/report')
def page_report():
    return render_template('report.html')

@app.route('/page/dashboard')
def page_dashboard():
    return render_template('dashboard.html')

@app.route('/page/code_generator')
def page_code_generator():
    return render_template('code_generator.html')

# @app.route('/page/admin_log')
# def page_code_generator():
#     return render_template('admin_log.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """上传CSV文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有选择文件'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'})

    if file and file.filename.lower().endswith('.csv'):
        # 基于内存流导入，不落盘
        file_bytes = file.read()
        result = data_manager.import_from_csv_bytes(file_bytes)
        return jsonify(result)

    return jsonify({'success': False, 'message': '只支持CSV文件'})

@app.route('/delete_csv', methods=['POST'])
def delete_csv():
    """删除（清空）所有已导入的CSV数据"""
    try:
        data_manager.clear_all_data()
        return jsonify({'success': True, 'message': '已清空所有CSV导入数据'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'清空失败: {str(e)}'})



@app.route('/analyze', methods=['GET'])
def analyze_data():
    """分析物流数据"""
    try:
        # 获取所有物流数据
        shipments = data_manager.get_all_shipments(limit=10000)

        if not shipments:
            return jsonify({'success': False, 'message': '没有可分析的数据，请先上传CSV文件'})

        # 获取每日统计
        daily_stats = data_manager.get_daily_stats()

        # 使用AI分析数据（使用asyncio.run执行异步代码）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis = loop.run_until_complete(model_handler.analyze_bulk_data(shipments))
            daily_report = loop.run_until_complete(model_handler.generate_daily_report(daily_stats, shipments))
        finally:
            loop.close()

        # 格式化响应
        analysis_html = format_ai_response(analysis['analysis'])
        report_html = format_ai_response(daily_report['report'])

        # 生成图表数据
        chart_data = _generate_chart_data(shipments, daily_stats)
        
        # 准备响应数据
        response_data = {
            'success': True,
            'analysis': analysis_html,
            'daily_report': report_html,
            'statistics': {
                **daily_stats,
                'surface_3d': chart_data['surface_3d'],
                'scatter_3d': chart_data['scatter_3d'],
                'wireframe_3d': chart_data['wireframe_3d'],
                'data_info': chart_data['data_info']
            },
            'summary': {
                'total_records': len(shipments),
                'status_distribution': model_handler._get_status_distribution(shipments)
            }
        }
        

        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({'success': False, 'message': f'分析失败: {str(e)}'})


@app.route('/shipments', methods=['GET'])
def get_shipments():
    """获取物流数据列表"""
    limit = request.args.get('limit', 100, type=int)
    shipments = data_manager.get_all_shipments(limit=limit)
    return jsonify({'success': True, 'data': shipments})


@app.route('/shipment/<shipment_id>', methods=['GET'])
def get_shipment(shipment_id):
    """获取单个物流详情和分析"""
    shipment = data_manager.get_shipment_by_id(shipment_id)
    if not shipment:
        return jsonify({'success': False, 'message': '未找到指定的物流信息'})

    events = data_manager.get_shipment_events(shipment_id)

    # 使用AI分析（使用asyncio.run执行异步代码）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        analysis = loop.run_until_complete(model_handler.analyze_shipment_data(shipment))
        prediction = loop.run_until_complete(model_handler.predict_delivery_time(shipment, events))
    finally:
        loop.close()

    # 格式化响应
    analysis_html = format_ai_response(analysis['analysis'])
    prediction_html = format_ai_response(prediction['prediction'])

    return jsonify({
        'success': True,
        'shipment': shipment,
        'events': events,
        'analysis': analysis_html,
        'prediction': prediction_html
    })


def _generate_chart_data(shipments, daily_stats):
    """生成三维曲面图数据"""
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')  # 使用非GUI后端
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import base64
    import io
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 调试信息
    print(f"收到 {len(shipments)} 条物流数据")
    if shipments:
        print(f"第一条数据字段: {list(shipments[0].keys())}")
        print(f"第一条数据示例: {shipments[0]}")
    
    def _parse_date_str(date_str):
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(str(date_str).replace('Z', '+00:00')).date()
        except Exception:
            try:
                return datetime.strptime(str(date_str), '%Y-%m-%d').date()
            except Exception:
                try:
                    return datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S').date()
                except Exception:
                    return None

    # 准备三维数据：时间 x 城市 x 状态
    time_city_status_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    for shipment in shipments:
        # 优先使用actual_delivery，如果为空则使用created_at
        delivery_date = _parse_date_str(shipment.get('actual_delivery'))
        if delivery_date is None:
            delivery_date = _parse_date_str(shipment.get('created_at'))
        
        # 如果还是没有日期，跳过这条记录
        if delivery_date is None:
            continue
            
        city = shipment.get('origin_city', '未知城市')
        status = shipment.get('status', '未知状态')
        
        # 确保城市和状态不为空
        if city and city != '未知城市' and status and status != '未知状态':
            time_city_status_data[delivery_date][city][status] += 1
    
    # 调试信息
    print(f"处理后的数据点数量: {sum(sum(sum(city_data.values()) for city_data in day_data.values()) for day_data in time_city_status_data.values())}")
    print(f"涉及的城市: {set(city for day_data in time_city_status_data.values() for city in day_data.keys())}")
    print(f"涉及的状态: {set(status for day_data in time_city_status_data.values() for city_data in day_data.values() for status in city_data.keys())}")
    
    # 获取数据范围
    if not time_city_status_data:
        # 如果没有数据，返回空结果
        return {
            'surface_3d': None,
            'scatter_3d': None,
            'wireframe_3d': None,
            'data_info': {
                'cities': [],
                'time_labels': [],
                'statuses': [],
                'error': '没有可用的数据生成三维图表'
            }
        }
    
    # 获取所有日期并排序
    all_dates = sorted(time_city_status_data.keys())
    if len(all_dates) > 7:
        # 如果数据超过7天，取最近7天
        last_7_days = all_dates[-7:]
    else:
        # 如果数据少于7天，使用所有可用日期
        last_7_days = all_dates
    
    all_cities = set()
    all_statuses = set()
    for day_data in time_city_status_data.values():
        for city in day_data.keys():
            all_cities.add(city)
            for status in day_data[city].keys():
                all_statuses.add(status)
    
    all_cities = sorted(list(all_cities))[:8]  # 限制前8个城市
    all_statuses = sorted(list(all_statuses))[:6]  # 限制前6个状态
    
    # 创建三维数据矩阵
    X = np.arange(len(all_cities))  # 城市索引
    Y = np.arange(len(last_7_days))  # 时间索引
    X, Y = np.meshgrid(X, Y)
    
    # 为每个状态创建Z值矩阵
    surface_data = {}
    for status in all_statuses:
        Z = np.zeros((len(last_7_days), len(all_cities)))
        for i, day in enumerate(last_7_days):
            for j, city in enumerate(all_cities):
                Z[i, j] = time_city_status_data[day][city][status]
        surface_data[status] = Z
    
    # 生成三维曲面图
    def create_3d_surface_plot():
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        
        for i, (status, Z) in enumerate(surface_data.items()):
            if i < len(colors):
                surf = ax.plot_surface(X, Y, Z, alpha=0.7, color=colors[i], 
                                     label=status, linewidth=0, antialiased=True)
        
        ax.set_xlabel('Cities')
        ax.set_ylabel('Time')
        ax.set_zlabel('Count')
        ax.set_title('3D Surface Plot - Logistics Data')
        
        # 设置坐标轴标签
        ax.set_xticks(range(len(all_cities)))
        ax.set_xticklabels(all_cities, rotation=45)
        ax.set_yticks(range(len(last_7_days)))
        ax.set_yticklabels([d.strftime('%m-%d') for d in last_7_days])
        
        plt.tight_layout()
        
        # 转换为base64字符串
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    # 生成三维散点图
    def create_3d_scatter_plot():
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        
        for i, (status, Z) in enumerate(surface_data.items()):
            if i < len(colors):
                # 创建散点数据
                x_data, y_data, z_data = [], [], []
                for row in range(Z.shape[0]):
                    for col in range(Z.shape[1]):
                        if Z[row, col] > 0:
                            x_data.append(col)
                            y_data.append(row)
                            z_data.append(Z[row, col])
                
                if x_data:
                    ax.scatter(x_data, y_data, z_data, c=colors[i], 
                             label=status, s=50, alpha=0.7)
        
        ax.set_xlabel('Cities')
        ax.set_ylabel('Time')
        ax.set_zlabel('Count')
        ax.set_title('3D Scatter Plot - Logistics Data')
        
        # 设置坐标轴标签
        ax.set_xticks(range(len(all_cities)))
        ax.set_xticklabels(all_cities, rotation=45)
        ax.set_yticks(range(len(last_7_days)))
        ax.set_yticklabels([d.strftime('%m-%d') for d in last_7_days])
        
        ax.legend()
        plt.tight_layout()
        
        # 转换为base64字符串
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    # 生成三维线框图
    def create_3d_wireframe_plot():
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
        
        for i, (status, Z) in enumerate(surface_data.items()):
            if i < len(colors):
                ax.plot_wireframe(X, Y, Z, color=colors[i], alpha=0.8, 
                                linewidth=1, label=status)
        
        ax.set_xlabel('Cities')
        ax.set_ylabel('Time')
        ax.set_zlabel('Count')
        ax.set_title('3D Wireframe Plot - Logistics Data')
        
        # 设置坐标轴标签
        ax.set_xticks(range(len(all_cities)))
        ax.set_xticklabels(all_cities, rotation=45)
        ax.set_yticks(range(len(last_7_days)))
        ax.set_yticklabels([d.strftime('%m-%d') for d in last_7_days])
        
        ax.legend()
        plt.tight_layout()
        
        # 转换为base64字符串
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    try:
        # 生成三种类型的三维图
        surface_plot = create_3d_surface_plot()
        scatter_plot = create_3d_scatter_plot()
        wireframe_plot = create_3d_wireframe_plot()
        
        return {
            'surface_3d': surface_plot,
            'scatter_3d': scatter_plot,
            'wireframe_3d': wireframe_plot,
            'data_info': {
                'cities': all_cities,
                'time_labels': [d.strftime('%m-%d') for d in last_7_days],
                'statuses': all_statuses,
                'surface_data': {k: v.tolist() for k, v in surface_data.items()}
            }
        }
    except Exception as e:
        print(f"生成三维图时出错: {e}")
        return {
            'surface_3d': None,
            'scatter_3d': None,
            'wireframe_3d': None,
            'data_info': {
                'cities': all_cities,
                'time_labels': [d.strftime('%m-%d') for d in last_7_days],
                'statuses': all_statuses,
                'error': str(e)
            }
        }


@app.route('/generate_code', methods=['POST'])
async def generate_code():
    """生成Python代码"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'message': '请输入问题'})
        
        # 获取物流数据作为上下文
        shipments = data_manager.get_all_shipments(limit=1000)
        
        # 构建代码生成提示词
        context = f"""
        你是一个Python数据分析专家。用户想要分析物流数据，请根据用户的问题生成相应的Python代码。
        
        可用的物流数据字段包括：
        - id: 物流单号
        - origin: 发货地
        - destination: 收货地
        - origin_city: 发货城市
        - destination_city: 收货城市
        - status: 物流状态
        - estimated_delivery: 预计送达时间
        - actual_delivery: 实际送达时间
        - weight: 重量
        - courier_company: 快递公司
        - shipping_fee: 运费
        - created_at: 创建时间
        
        数据样本（前5条）：
        {shipments[:5] if shipments else '暂无数据'}
        
        请生成完整的Python代码，包括：
        1. 导入必要的库（pandas, matplotlib, seaborn等）
        2. 数据加载和处理
        3. 数据分析和可视化
        4. 结果输出
        
        代码应该能够直接运行，并且包含适当的错误处理。
        """
        
        prompt = f"""
        用户问题：{question}
        
        请生成Python代码来分析物流数据。代码应该：
        - 使用pandas处理数据
        - 使用matplotlib或seaborn进行可视化
        - 包含适当的注释
        - 能够处理空数据和异常情况
        - 输出清晰的分析结果
        
        只返回Python代码，不要包含其他说明文字。
        """
        
        # 使用AI生成代码
        code = await model_handler.generate_response(prompt, context)
        
        # 清理代码（移除可能的markdown标记）
        if code.startswith('```python'):
            code = code[9:]
        if code.startswith('```'):
            code = code[3:]
        if code.endswith('```'):
            code = code[:-3]
        
        code = code.strip()
        

        
        return jsonify({
            'success': True,
            'code': code
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成代码失败: {str(e)}'
        })


@app.route('/execute_code', methods=['POST'])
def execute_code():
    """执行Python代码"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'success': False, 'error': '没有提供代码'})
        
        # 创建安全的执行环境
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'min': min,
                'max': max,
                'sum': sum,
                'sorted': sorted,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'abs': abs,
                'round': round,
                'type': type,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'open': open,
                '__import__': __import__,
            }
        }
        
        # 添加常用的数据分析库
        try:
            import pandas as pd
            import numpy as np
            import matplotlib.pyplot as plt
            import seaborn as sns
            from datetime import datetime, timedelta
            import json
            
            safe_globals.update({
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'datetime': datetime,
                'timedelta': timedelta,
                'json': json,
                'shipments': data_manager.get_all_shipments(limit=10000)  # 提供数据
            })
        except ImportError as e:
            return jsonify({
                'success': False,
                'error': f'缺少必要的库: {str(e)}'
            })
        
        # 捕获输出
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_output = io.StringIO()
        sys.stderr = captured_error = io.StringIO()
        
        try:
            # 执行代码
            exec(code, safe_globals)
            
            # 获取输出
            output = captured_output.getvalue()
            error = captured_error.getvalue()
            
            if error:

                
                return jsonify({
                    'success': False,
                    'error': f'执行错误:\n{error}'
                })
            

            
            return jsonify({
                'success': True,
                'output': output or '代码执行成功，无输出内容'
            })
            
        except Exception as e:
            error_msg = f'代码执行异常:\n{str(e)}\n\n{traceback.format_exc()}'

            
            return jsonify({
                'success': False,
                'error': error_msg
            })
        
        finally:
            # 恢复标准输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
    except Exception as e:

        
        return jsonify({
            'success': False,
            'error': f'执行请求失败: {str(e)}'
        })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)