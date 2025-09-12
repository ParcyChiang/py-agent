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


@app.route('/analyze', methods=['GET'])
async def analyze_data():
    """分析物流数据"""
    try:
        # 获取所有物流数据
        shipments = data_manager.get_all_shipments(limit=10000)

        if not shipments:
            return jsonify({'success': False, 'message': '没有可分析的数据，请先上传CSV文件'})

        # 获取每日统计
        daily_stats = data_manager.get_daily_stats()

        # 使用AI分析数据
        analysis = await model_handler.analyze_bulk_data(shipments)
        daily_report = await model_handler.generate_daily_report(daily_stats, shipments)

        # 格式化响应
        analysis_html = format_ai_response(analysis['analysis'])
        report_html = format_ai_response(daily_report['report'])

        # 生成图表数据
        chart_data = _generate_chart_data(shipments, daily_stats)
        
        return jsonify({
            'success': True,
            'analysis': analysis_html,
            'daily_report': report_html,
            'statistics': {
                **daily_stats,
                'trend_data': chart_data['trend_data'],
                'location_data': chart_data['location_data']
            },
            'summary': {
                'total_records': len(shipments),
                'status_distribution': model_handler._get_status_distribution(shipments)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'分析失败: {str(e)}'})


@app.route('/shipments', methods=['GET'])
def get_shipments():
    """获取物流数据列表"""
    limit = request.args.get('limit', 100, type=int)
    shipments = data_manager.get_all_shipments(limit=limit)
    return jsonify({'success': True, 'data': shipments})


@app.route('/shipment/<shipment_id>', methods=['GET'])
async def get_shipment(shipment_id):
    """获取单个物流详情和分析"""
    shipment = data_manager.get_shipment_by_id(shipment_id)
    if not shipment:
        return jsonify({'success': False, 'message': '未找到指定的物流信息'})

    events = data_manager.get_shipment_events(shipment_id)

    # 使用AI分析
    analysis = await model_handler.analyze_shipment_data(shipment)
    prediction = await model_handler.predict_delivery_time(shipment, events)

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
    """生成图表数据"""
    # 趋势数据 - 按日期统计
    trend_data = defaultdict(int)
    for shipment in shipments:
        if 'created_at' in shipment:
            try:
                date = datetime.fromisoformat(shipment['created_at'].replace('Z', '+00:00')).date()
                trend_data[date] += 1
            except:
                continue
    
    # 按日期排序并生成趋势数据
    sorted_dates = sorted(trend_data.keys())
    trend_labels = [date.strftime('%m-%d') for date in sorted_dates[-7:]]  # 最近7天
    trend_values = [trend_data[date] for date in sorted_dates[-7:]]
    
    # 地理位置数据
    location_counter = Counter()
    for shipment in shipments:
        if 'origin_city' in shipment and shipment['origin_city']:
            location_counter[shipment['origin_city']] += 1
    
    # 取前5个城市
    top_locations = location_counter.most_common(5)
    location_labels = [loc[0] for loc in top_locations]
    location_values = [loc[1] for loc in top_locations]
    
    return {
        'trend_data': {
            'labels': trend_labels,
            'data': trend_values
        },
        'location_data': {
            'labels': location_labels,
            'data': location_values
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