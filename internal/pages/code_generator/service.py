# pages/code_generator/service.py
"""代码生成页面服务层"""
import asyncio
import sys
import io
import builtins
import traceback
from typing import Dict, Any

from internal.pages.upload.dao import ShipmentDAO
from internal.models.model_handler import MiniMaxModelHandler


class CodeGenService:
    """代码生成服务"""

    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = MiniMaxModelHandler()

    async def generate_code(self, question: str) -> Dict[str, Any]:
        """生成 Python 代码"""
        if not question:
            return {'success': False, 'message': '请输入问题'}

        shipments, _ = self.shipment_dao.get_all_shipments(limit=1000)

        context = self._build_code_generation_context(shipments)

        prompt = f"""用户问题：{question}

请根据上述信息生成Python代码。只返回可运行的Python代码，不要包含任何说明文字、注释或markdown标记。代码应该能够直接在提供的沙箱环境中执行。"""

        code = await self.model_handler.generate_response(prompt, context)

        if code.startswith('```python'):
            code = code[9:]
        if code.startswith('```'):
            code = code[3:]
        if code.endswith('```'):
            code = code[:-3]

        code = code.strip()

        return {'success': True, 'code': code}

    def execute_code(self, code: str) -> Dict[str, Any]:
        """执行 Python 代码"""
        if not code:
            return {'success': False, 'error': '没有提供代码'}

        _allowed_builtins = {
            'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'tuple', 'set',
            'min', 'max', 'sum', 'sorted', 'range', 'enumerate', 'zip', 'map',
            'filter', 'abs', 'round', 'type', 'isinstance', 'hasattr', 'getattr',
            'setattr', '__import__'
        }
        safe_builtins = {name: getattr(builtins, name) for name in _allowed_builtins if hasattr(builtins, name)}
        if '__import__' not in safe_builtins:
            safe_builtins['__import__'] = builtins.__import__

        try:
            import pandas as pd
            import numpy as np
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            from datetime import datetime, timedelta
            import json

            from internal.pkg.utils import configure_matplotlib
            configure_matplotlib()

            safe_globals = {
                '__builtins__': safe_builtins,
                'pd': pd,
                'np': np,
                'plt': plt,
                'sns': sns,
                'datetime': datetime,
                'timedelta': timedelta,
                'json': json,
                'shipments': self.shipment_dao.get_all_shipments(limit=10000)[0]
            }
        except ImportError as e:
            return {'success': False, 'error': f'缺少必要的库: {str(e)}'}

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = captured_output = io.StringIO()
        sys.stderr = captured_error = io.StringIO()

        try:
            exec(code, safe_globals)

            output = captured_output.getvalue()
            error = captured_error.getvalue()

            if error:
                return {'success': False, 'error': f'执行错误:\n{error}'}

            image_data = None
            for key in ['img_base64', 'image_base64', 'img_data', 'img_buffer']:
                if key in safe_globals:
                    val = safe_globals[key]
                    if isinstance(val, (str, bytes)) and len(str(val)) > 100:
                        if hasattr(val, 'getvalue'):
                            val = val.getvalue()
                        if isinstance(val, bytes):
                            import base64 as b64_module
                            try:
                                image_data = b64_module.b64encode(val).decode('ascii')
                                break
                            except:
                                pass
                        elif isinstance(val, str) and len(val) > 100:
                            image_data = val
                            break

            result = {'success': True, 'output': output or '代码执行成功，无输出内容'}
            if image_data:
                result['image'] = image_data

            return result

        except Exception as e:
            error_msg = f'代码执行异常:\n{str(e)}\n\n{traceback.format_exc()}'
            return {'success': False, 'error': error_msg}

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _build_code_generation_context(self, shipments: list) -> str:
        """构建代码生成上下文"""
        return f"""
你是一个Python数据分析专家，专注于物流数据分析。

## 可用的物流数据字段
- id: 物流单号
- origin: 发货地
- origin_city: 发货城市
- destination: 收货地
- destination_city: 收货城市
- status: 物流状态
- estimated_delivery: 预计送达时间
- actual_delivery: 实际送达时间
- weight: 重量
- courier_company: 快递公司
- shipping_fee: 运费
- created_at: 创建时间

## 数据样本（前5条）
{shipments[:5] if shipments else '暂无数据'}

## 重要说明
- 数据已经存在于 `shipments` 变量中（类型：list of dict），不需要重新加载
- `shipments` 变量可以直接使用，无需导入或读取
- 代码中可以直接使用 `pd.DataFrame(shipments)` 将数据转为 DataFrame

## 可用的库和函数
- pandas (pd): 数据处理
- numpy (np): 数值计算
- matplotlib.pyplot (plt): 绘图
- seaborn (sns): 高级可视化
- datetime, timedelta: 时间处理
- json: JSON处理
- 所有基础函数：print, len, str, int, float, list, dict, range, sorted, sum, min, max, zip, map, filter 等

## 输出要求
- 使用 print() 输出分析结果
- **图表标题和标签请使用英文**，避免中文字体问题
- 如果需要生成图像，使用 plt.savefig() 保存到 BytesIO 缓冲区，然后 base64 编码输出
- 不要使用 input() 函数
- 不要使用 open() 进行文件读写
- 不要导入 os, subprocess, sys, pathlib 等系统模块
- 添加适当的错误处理，处理空数据情况
"""
