#!/usr/bin/env python3
"""测试分析端点的中文数据返回"""
import requests
import json

# 设置 Flask 应用的 URL
BASE_URL = 'http://127.0.0.1:5000'

def test_analyze_endpoint():
    """测试/analyze端点返回的数据是否包含中文状态"""
    print("测试分析端点...")
    
    try:
        response = requests.get(f'{BASE_URL}/analyze')
        
        if response.status_code == 200:
            data = response.json()
            print(f"状态: {'成功' if data['success'] else '失败'}")
            
            if data['success']:
                print("\n数据统计:")
                print(f"  总发货量: {data['statistics']['total_shipments']}")
                
                print("\n状态分布:")
                for status, count in data['summary']['status_distribution'].items():
                    print(f"  {status}: {count}")
                
                print("\n三维数据信息:")
                data_info = data['statistics']['data_info']
                print(f"  城市列表: {', '.join(data_info['cities'])}")
                print(f"  时间范围: {', '.join(data_info['time_labels'])}")
                print(f"  状态类型: {', '.join(data_info['statuses'])}")
                
                print("\n数据矩阵预览:")
                for status, matrix in data_info['surface_data'].items():
                    print(f"  {status}:")
                    print(f"    矩阵大小: {len(matrix)} x {len(matrix[0])}")
                    print(f"    最大值: {max([max(row) for row in matrix])}")
                    print(f"    总和: {sum([sum(row) for row in matrix])}")
            else:
                print(f"  错误信息: {data['message']}")
        else:
            print(f"HTTP错误: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("连接错误: 请确保 Flask 应用正在运行在 http://127.0.0.1:5000")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_analyze_endpoint()
