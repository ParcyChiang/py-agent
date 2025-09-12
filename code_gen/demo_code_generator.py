#!/usr/bin/env python3
"""
代码生成器演示脚本
展示如何使用Python代码生成和执行功能
"""

import requests
import json

def test_code_generation():
    """测试代码生成功能"""
    print("🚀 测试代码生成功能...")
    
    # 测试问题
    questions = [
        "分析物流数据中不同状态的包裹数量分布，并生成饼图",
        "计算每个城市的平均配送时间，并找出配送时间最长的前5个城市",
        "分析不同快递公司的配送效率，比较它们的平均配送时间和成功率"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 问题 {i}: {question}")
        
        # 发送代码生成请求
        response = requests.post(
            'http://localhost:5000/generate_code',
            headers={'Content-Type': 'application/json'},
            json={'question': question}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ 代码生成成功")
                print("📄 生成的代码片段:")
                code = result['code']
                # 只显示前200个字符
                print(code[:200] + "..." if len(code) > 200 else code)
            else:
                print(f"❌ 代码生成失败: {result['message']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")

def test_code_execution():
    """测试代码执行功能"""
    print("\n🔧 测试代码执行功能...")
    
    # 测试代码
    test_codes = [
        {
            "name": "简单输出测试",
            "code": 'print("Hello, 代码执行器!")\nprint("当前时间:", __import__("datetime").datetime.now())'
        },
        {
            "name": "物流数据统计",
            "code": '''
import pandas as pd
print("📊 物流数据统计报告")
print("=" * 40)
print(f"总记录数: {len(shipments)}")

if shipments:
    df = pd.DataFrame(shipments)
    print(f"数据列数: {len(df.columns)}")
    print(f"状态分布:")
    status_counts = df["status"].value_counts()
    for status, count in status_counts.head(5).items():
        print(f"  {status}: {count}")
    
    print(f"\\n城市分布 (前5个):")
    city_counts = df["origin_city"].value_counts()
    for city, count in city_counts.head(5).items():
        print(f"  {city}: {count}")
else:
    print("❌ 暂无数据")
'''
        }
    ]
    
    for test in test_codes:
        print(f"\n🧪 {test['name']}")
        
        # 发送代码执行请求
        response = requests.post(
            'http://localhost:5000/execute_code',
            headers={'Content-Type': 'application/json'},
            json={'code': test['code']}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ 代码执行成功")
                print("📤 输出结果:")
                print(result['output'])
            else:
                print(f"❌ 代码执行失败: {result['error']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")

def main():
    """主函数"""
    print("🎯 Python代码生成器演示")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print("❌ 服务器响应异常")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务器，请确保应用程序正在运行")
        print("   运行命令: python3 app.py")
        return
    
    # 运行测试
    test_code_generation()
    test_code_execution()
    
    print("\n🎉 演示完成！")
    print("💡 您可以在浏览器中访问 http://localhost:5000/page/code_generator 使用完整功能")

if __name__ == "__main__":
    main()
