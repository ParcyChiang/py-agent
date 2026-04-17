## py-agent搭建Log
### v1.11
1. refactor: 项目目录结构重构，pages→service，models→pkg/models，config→configs

### v1.10
1. refactor: 路由重构，各 page 模块的 http.py 统一通过 routes() 方法注册路由，router/__init__.py 简化
2. refactor: 项目结构从 server/handler/models 重构为 pages/xxx/(http|service|dao) 分层架构
3. fix: 修复日报中心模板使用 /analyze 接口的问题，改为 /report

### v1.9
1. fix: 修复 `login_required` 装饰器不支持 async 函数的问题，对比分析等功能恢复正常

### v1.8
1. refactor: 将 `charts/`、`utils/`、`config.py`、`response.py`、`constants.py` 移动到 `internal/pkg/`
2. refactor: 更新所有 internal 模块的 import 路径
3. refactor: 更新 `.gitignore`，忽略 `docs/`、`data/csv_gen/*` 但保留 `generate_logistics_data.py`
4. docs: 更新 `README.md` 目录结构，反映 internal/pkg/ 共享模块结构

### v1.7
1. perf: 三维图表添加数据采样，数据超过100条时随机采样到100条，避免渲染卡顿
2. perf: 散点图改为按城市分组批量绘制，替代逐点绘制，大幅提升渲染性能
3. fix: 移除 plt.tight_layout() 避免 Tight layout not applied 警告
4. perf: 三维图表 DPI 从 150 降至 100，加快图像生成速度
5. fix: 修复 /chart_data API 返回结构，添加 summary.status_distribution 以适配前端

### v1.6
1. refactor: 重构项目为 HTTP/Server/DAO 三层架构
2. refactor: 创建 `internal/` 目录，组织 handler/server/models/middleware/router 层
3. refactor: 创建 `internal/pkg/` 目录，存放共享模块 config/response/charts/utils/constants
4. refactor: `app.py` 简化为 Flask 入口，路由注册移至 `internal/router/`
5. refactor: DAO 层拆分至 `internal/models/shipment.py`, `user.py`, `log.py`
6. refactor: Server 层创建 `internal/server/shipment.py`, `auth.py`, `analysis.py`, `dashboard.py`, `code_gen.py`
7. refactor: Handler 层创建 `internal/handler/*.py` 处理 HTTP 请求
8. refactor: 中间件移至 `internal/middleware/`，包含认证和日志
9. refactor: 更新所有内部 import 路径

### v1.5
1. refactor: 将 `safe_float`, `safe_str`, `safe_date` 从 `models/__init__.py` 提取到 `utils/__init__.py`
2. refactor: 移除 `models/__init__.py` 中 `import_from_csv` 和 `import_from_csv_bytes` 方法内重复的函数定义
3. refactor: 创建 `constants.py` 统一管理 `STATUS_CN_MAP` 常量
4. refactor: `models/__init__.py` 和 `app.py` 从 `constants.py` 导入 `STATUS_CN_MAP`
5. refactor: 简化 `_parse_date_str` 函数逻辑
6. refactor: 提取 `configure_matplotlib` 到 `utils/__init__.py`，统一 matplotlib 中文字体配置
7. refactor: 引入 `get_connection` 上下文管理器，简化约14个方法的数据库连接管理
8. refactor: 将图表生成逻辑分离到 `charts/` 模块（surface/scatter/wireframe）

### v1.4
1. fix: code_generator沙箱环境修复,代码生成与图像生成

### v1.3
1. feat: compare适配毛玻璃效果
2. feat: compare接收回调适配markdown
3. feat: compare.select下拉框提前获取表中数据
4. fix: compare 点击 X 清除后会自动触发搜索，展示新的结果
5. fix: compare缓存

### v1.2
1. feat: upload页面新增分页器，默认每页10条数据
2. refactor: 合并upload与shipments页面，导入CSV后自动加载物流数据

### v1.1.1
1. refactor: 合并upload与shipments页面，导入CSV后自动加载物流数据
2. refactor: 新增运营报告页面(/page/analysis_report)，解耦AI分析与三维图表
3. refactor: analyze页面改用/chart_data API，不再调用AI

### v1.1
1. refactor: 新增运营报告页面(/page/analysis_report)，解耦AI分析与三维图表
2. refactor: analyze页面改用/chart_data API，不再调用AI

### v1.0.0
1.feat: 答辩前发布1.0.0版本

### v0.2.3
1. feat:  趋势图可以切换不同的时间粒度(天,周,月)（待优化）

### v0.2.2
1. feat:  更改二维图表为三维曲面图

### v0.2.1
1. feat: 更新 toDO.md
2. feat: 更新 论文题目

### v0.2
1. feat: 可视化图标,但是还有今日交付率不显示的 bug
2. feat: 生成 python 代码并运行,但是人工智障
3. feat: 添加删除 csv 的按钮
4. feat: 使用 mqsql 存储
5. feat: 添加"待完善"任务列表,罗列目前遇到的小问题
6. fix: 修复了运营分析页面的交付时间趋势无数据的 bug
7. fix: 修复了实时监控页面的总发货量、今日交付、运输中、交付率不对的 bug

### v0.1.2
1. feat:每次导入的 csv 都能被运行,但是 upload 文件夹还不能被解决
2. fix:移除了 uploads 文件夹
3. fix:更新了提交规则, 更新了 readme
4. fix:更新了依赖,更新了 readme

### v0.1.1
1. feat:更改为qwen:0.5b模型，响应迅速
2. fix:修复了每日运营无法解答的bug
3. fix:修复了ai只统计前100天的bug

### v0.1
1. feat:网页实现，但是ai响应速度慢

### v0.0.2
1. feat:基础代码

### v0.0.1
1. feat:框架搭建