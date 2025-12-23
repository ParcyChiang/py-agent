#!/usr/bin/env python3
"""测试三维图表生成功能"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
from datetime import datetime
from app import _generate_chart_data

def load_test_data(filename):
    """从CSV文件加载测试数据"""
    data = []
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # 将相关字段转换为适当的格式
            row['weight'] = float(row['weight']) if row['weight'] else 0
            row['shipping_fee'] = float(row['shipping_fee']) if row['shipping_fee'] else 0
            data.append(row)
    return data

if __name__ == "__main__":
    print("开始测试三维图表生成功能...")
    
    # 使用刚刚生成的测试数据
    test_file = os.path.join('csv_gen', 'logistics_sample_100.csv')
    
    if not os.path.exists(test_file):
        print(f"错误：测试文件 {test_file} 不存在")
        sys.exit(1)
    
    # 加载测试数据
    shipments = load_test_data(test_file)
    print(f"成功加载 {len(shipments)} 条测试数据")
    
    # 创建模拟的 daily_stats
    daily_stats = {
        'total_shipments': len(shipments),
        'delivered_shipments': len([s for s in shipments if s['status'] == 'delivered']),
        'avg_delivery_time': 2.5,
        'avg_weight': 5.0,
        'avg_shipping_fee': 30.0
    }
    
    print("开始生成三维图表数据...")
    
    try:
        # 调用 _generate_chart_data 函数
        result = _generate_chart_data(shipments, daily_stats)
        
        print("\n=== 三维图表生成结果 ===")
        print(f"三维曲面图: {'已生成' if result['surface_3d'] else '未生成'}")
        print(f"三维散点图: {'已生成' if result['scatter_3d'] else '未生成'}")
        print(f"三维线框图: {'已生成' if result['wireframe_3d'] else '未生成'}")
        
        print("\n=== 数据信息 ===")
        print(f"城市: {result['data_info']['cities']}")
        print(f"时间标签: {result['data_info']['time_labels']}")
        print(f"状态: {result['data_info']['statuses']}")
        
        if result['data_info'].get('error'):
            print(f"\n错误信息: {result['data_info']['error']}")
        else:
            print(f"\n数据矩阵: {len(result['data_info']['surface_data'].keys())} 个状态")
            
    except Exception as e:
        print(f"\n生成三维图时发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n测试完成")
