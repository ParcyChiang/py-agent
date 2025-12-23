#!/usr/bin/env python3
"""测试中文状态转换功能"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
from datetime import datetime, date, timedelta
from collections import defaultdict

# 测试状态转换功能
def test_status_conversion():
    """测试英文状态到中文状态的转换"""
    print("测试状态转换...")
    
    # 复制 _generate_chart_data 函数中的状态映射
    status_cn_map = {
        'delivered': '已送达',
        'failed_delivery': '配送失败',
        'in_transit': '运输中',
        'out_for_delivery': '派件中',
        'pending': '待处理',
        'picked_up': '已揽件'
    }
    
    # 测试所有预设状态
    test_states = ['delivered', 'failed_delivery', 'in_transit', 
                  'out_for_delivery', 'pending', 'picked_up', 
                  'unknown_status']  # 包含一个未知状态
    
    for state in test_states:
        converted = status_cn_map.get(state, state)
        print(f"  {state!r} -> {converted!r}")
    
    print("状态转换测试完成")

if __name__ == "__main__":
    # 运行测试
    test_status_conversion()
    
    print("\n所有测试完成")
