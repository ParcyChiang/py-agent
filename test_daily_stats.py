#!/usr/bin/env python3
"""测试 get_daily_stats 函数返回的数据结构"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import create_data_manager

if __name__ == "__main__":
    print("测试 get_daily_stats 函数...")
    
    data_manager = create_data_manager()
    stats = data_manager.get_daily_stats()
    
    print(f"get_daily_stats 返回: {stats}")
    print(f"数据类型: {type(stats)}")
    print(f"总运单数: {stats.get('total_shipments')}")
    print(f"已送达: {stats.get('delivered')}")
    print(f"平均送达时间: {stats.get('avg_delivery_time')}")
    print(f"所有键: {list(stats.keys())}")
