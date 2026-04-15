#!/usr/bin/env python3
"""上传测试CSV文件到应用"""
import requests

def upload_csv_file(file_path):
    """上传CSV文件到应用"""
    url = "http://localhost:5000/upload"
    
    print(f"上传文件: {file_path}")
    
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (file_path, file, 'text/csv')}
            response = requests.post(url, files=files)
            
        print(f"响应状态: {response.status_code}")
        print(f"响应内容: {response.json()}")
        
    except Exception as e:
        print(f"上传失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    csv_path = "/Users/rubyjiang/py-agent/csv_gen/logistics_sample_100.csv"
    upload_csv_file(csv_path)
