# Python代码生成器功能说明

## 功能概述

新增的Python代码生成器功能允许用户通过自然语言描述分析需求，AI会自动生成相应的Python代码，并可以在安全的沙箱环境中执行这些代码。

## 主要特性

### 1. 智能代码生成
- 用户可以用自然语言描述分析需求
- AI基于物流数据结构和上下文生成Python代码
- 支持pandas、matplotlib、seaborn等数据分析库
- 自动处理数据加载、分析和可视化

### 2. 安全代码执行
- 使用沙箱环境执行生成的代码
- 限制危险操作，确保系统安全
- 提供完整的错误处理和异常捕获
- 支持实时输出和结果展示

### 3. 丰富的示例
- 内置多个示例问题，帮助用户快速上手
- 涵盖数据统计、可视化、趋势分析等常见场景
- 支持自定义问题输入

## 使用方法

### 1. 访问代码生成器页面
在浏览器中访问：`http://localhost:5000/page/code_generator`

### 2. 输入分析需求
在文本框中描述您想要的分析任务，例如：
- "分析物流数据中不同状态的包裹数量分布，并生成饼图"
- "计算每个城市的平均配送时间，并找出配送时间最长的前5个城市"
- "分析不同快递公司的配送效率，比较它们的平均配送时间和成功率"

### 3. 生成代码
点击"🤖 生成Python代码"按钮，AI将根据您的需求生成相应的Python代码。

### 4. 执行代码
点击"▶️ 执行代码"按钮，在安全环境中执行生成的代码并查看结果。

## 技术实现

### 后端API
- `POST /generate_code`: 生成Python代码
- `POST /execute_code`: 执行Python代码

### 安全措施
- 限制可用的内置函数和模块
- 使用沙箱环境隔离代码执行
- 捕获并处理所有异常
- 限制执行时间和资源使用

### 支持的数据分析库
- pandas: 数据处理和分析
- numpy: 数值计算
- matplotlib: 基础绘图
- seaborn: 统计可视化
- datetime: 时间处理

## 示例代码

### 状态分布分析
```python
import pandas as pd
import matplotlib.pyplot as plt

# 将数据转换为DataFrame
df = pd.DataFrame(shipments)

# 统计状态分布
status_counts = df['status'].value_counts()

# 生成饼图
plt.figure(figsize=(10, 6))
status_counts.plot(kind='pie', autopct='%1.1f%%')
plt.title('物流状态分布')
plt.show()

print("状态分布统计:")
print(status_counts)
```

### 城市配送效率分析
```python
import pandas as pd
from datetime import datetime

# 将数据转换为DataFrame
df = pd.DataFrame(shipments)

# 计算配送时间
df['created_at'] = pd.to_datetime(df['created_at'])
df['actual_delivery'] = pd.to_datetime(df['actual_delivery'])
df['delivery_time'] = (df['actual_delivery'] - df['created_at']).dt.days

# 按城市分组计算平均配送时间
city_delivery = df.groupby('origin_city')['delivery_time'].agg(['mean', 'count']).round(2)
city_delivery = city_delivery[city_delivery['count'] >= 5]
city_delivery = city_delivery.sort_values('mean')

print("各城市平均配送时间（天）:")
print(city_delivery.head(10))
```

## 注意事项

1. **数据安全**: 代码执行在沙箱环境中进行，不会影响系统文件
2. **性能限制**: 代码执行有时间和资源限制，避免无限循环
3. **错误处理**: 所有异常都会被捕获并显示给用户
4. **依赖管理**: 确保已安装所需的数据分析库

## 故障排除

### 常见问题
1. **代码生成失败**: 检查问题描述是否清晰，尝试更具体的描述
2. **代码执行错误**: 检查生成的代码语法，确保逻辑正确
3. **缺少依赖**: 确保已安装所有必需的Python库

### 调试技巧
- 使用简单的测试代码验证执行环境
- 分步骤执行复杂代码
- 查看详细的错误信息进行调试

## 更新日志

- **v1.0.0**: 初始版本，支持基础代码生成和执行功能
- 支持pandas、matplotlib、seaborn等数据分析库
- 实现安全的代码执行沙箱
- 添加丰富的示例和错误处理
