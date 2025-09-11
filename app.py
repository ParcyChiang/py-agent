import os
import asyncio
import uuid
import atexit
import signal
from flask import Flask, render_template, request, jsonify

# 直接从models模块导入创建函数和类
from models import create_data_manager, create_model_handler
from utils import format_ai_response

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

# 使用工厂函数创建实例
data_manager = create_data_manager()
model_handler = create_model_handler()


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


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

        return jsonify({
            'success': True,
            'analysis': analysis_html,
            'daily_report': report_html,
            'statistics': daily_stats,
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)