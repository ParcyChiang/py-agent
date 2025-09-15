# py-agent
# 基于多模型物流数据分析及预测

一个用于分析与可视化物流运输数据的轻量级 Web 应用（Flask）。

## 功能特性
- **数据上传**：支持上传 CSV 物流数据并入库分析
- **可视化与报表**：在 `report`、`analyze` 页面查看统计与图表
- **发运记录浏览**：`shipments` 页面分页查看与筛选
- **示例数据生成**：`csv_gen/generate_logistics_data.py` 可批量生成样例 CSV

## 环境要求
- Python 3.9+（建议 3.10/3.11）
- macOS / Linux / Windows 任一

## 安装与启动
1. 克隆仓库
   ```bash
   git clone git@github.com:ParcyChiang/py-agent.git
   ```
2. 建议使用虚拟环境
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows 使用: .venv\\Scripts\\activate
   ```
3. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
4. #### 下载模型(重要!!!!!!)
    ```bash
   ollama pull qwen:0.5b
   ```
5. 运行应用
   ```bash
   python app.py
   ```
   默认在 `http://127.0.0.1:5000` 启动。访问首页以进入各功能页面。

## 目录结构
```text
py-agent/
├─ app.py                     # Flask 入口
├─ models/                    # 数据模型与数据库相关
├─ templates/                 # 前端模板 (Jinja2)
├─ static/                    # 静态资源
├─ csv_gen/                   # 示例数据与生成脚本
├─ code_gen/                  # Python 代码生成演示函数
├─ logistics.db               # SQLite 数据库（开发环境）
├─ requirements.txt           # Python 依赖
├─ CHANGELOG.md
└─ README.md
```

## 数据与数据库
- 项目默认使用 SQLite 数据库文件 `logistics.db` 存储数据。
- 首次运行时，如果数据库或表不存在，应用会在需要时自动创建（具体逻辑见 `models/__init__.py`）。

## 上传与示例数据
- 通过脚本生成自定义规模数据：
  ```bash
  python csv_gen/generate_logistics_data.py --rows 20000 --out my_logistics.csv
  ```
- 你可以在页面中上传 CSV 文件进行分析，或使用 `csv_gen` 目录下的样例：
  - `logistics_sample_100.csv`
  - `logistics_sample_1000.csv`
  - `logistics_sample_5000.csv`
  - `logistics_sample_10000.csv`


