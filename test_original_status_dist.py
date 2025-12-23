#!/usr/bin/env python3
"""查看原始数据中的状态分布"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import LogisticsDataManager

def test_original_status_distribution():
    """测试原始物流数据中的状态分布"""
    print("查看原始状态分布...")
    
    # 创建 LogisticsDataManager 实例
    data_manager = LogisticsDataManager('data/logistics.csv')
    
    # 检查是否有数据
    if not data_manager.data:
        print("没有数据加载")
        return
    
    print(f"数据总条数: {len(data_manager.data)}")
    
    # 获取所有状态
    all_statuses = [row['status'] for row in data_manager.data]
    status_counts = {}
    
    for status in all_statuses:
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("原始状态分布:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # 查看几条记录
    print("\n查看前5条记录:")
    for i, row in enumerate(data_manager.data[:5]):
        print(f"  记录 {i+1}: {row}")

if __name__ == "__main__":
    test_original_status_distribution()
