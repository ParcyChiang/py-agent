#!/usr/bin/env python3
"""测试 /analyze 端点返回的三维图数据"""
import requests
import json

# 应用的URL
BASE_URL = "http://localhost:5000"

def test_analyze_endpoint():
    """测试分析端点"""
    print("测试分析端点...")
    
    try:
        response = requests.get(f"{BASE_URL}/analyze")
        
        if response.status_code == 200:
            result = response.json()
            print(f"状态: {result.get('success')}")
            
            if result.get('success'):
                print("\n=== 统计数据 ===")
                print(f"总运单数: {result['statistics'].get('total_shipments')}")
                print(f"已送达运单数: {result['statistics'].get('delivered_shipments')}")
                print(f"平均送达时间: {result['statistics'].get('avg_delivery_time')}")
                
                print("\n=== 三维图数据 ===")
                print(f"三维曲面图: {'有数据' if result['statistics'].get('surface_3d') else '无数据'}")
                print(f"三维散点图: {'有数据' if result['statistics'].get('scatter_3d') else '无数据'}")
                print(f"三维线框图: {'有数据' if result['statistics'].get('wireframe_3d') else '无数据'}")
                
                print("\n=== 数据信息 ===")
                data_info = result['statistics'].get('data_info', {})
                print(f"城市数量: {len(data_info.get('cities', []))}")
                print(f"时间标签数量: {len(data_info.get('time_labels', []))}")
                print(f"状态数量: {len(data_info.get('statuses', []))}")
                print(f"错误信息: {data_info.get('error')}")
            else:
                print(f"错误: {result.get('message')}")
        else:
            print(f"HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
    
    except Exception as e:
        print(f"请求失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试分析端点")
    print(f"应用地址: {BASE_URL}")
    test_analyze_endpoint()
