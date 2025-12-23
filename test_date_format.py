#!/usr/bin/env python3
"""测试数据库中返回的日期格式"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import create_data_manager

if __name__ == "__main__":
    print("测试数据库返回的日期格式...")
    
    # 创建数据管理器实例
    data_manager = create_data_manager()
    
    # 获取所有运单数据
    shipments = data_manager.get_all_shipments()
    print(f"获取到 {len(shipments)} 条记录")
    
    if shipments:
        print("\n=== 日期字段测试 ===")
        sample = shipments[0]
        print(f"记录ID: {sample['id']}")
        print(f"created_at: {sample['created_at']}, 类型: {type(sample['created_at'])}")
        print(f"actual_delivery: {sample['actual_delivery']}, 类型: {type(sample['actual_delivery'])}")
        print(f"estimated_delivery: {sample['estimated_delivery']}, 类型: {type(sample['estimated_delivery'])}")
        
        print("\n=== 前几条记录的日期信息 ===")
        for i, shipment in enumerate(shipments[:5]):
            print(f"第 {i+1} 条:")
            print(f"  创建时间: {shipment['created_at']}")
            print(f"  实际交付时间: {shipment['actual_delivery']}")
            print(f"  预计交付时间: {shipment['estimated_delivery']}")
