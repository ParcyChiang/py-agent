# pages/analysis_report/service.py
"""分析报告页面服务层"""
import asyncio
from typing import Dict, Any

from internal.pkg.dao import ShipmentDAO
from internal.pkg.models.model_handler import AIModelHandler
from internal.pkg.utils import format_ai_response


class AnalysisReportService:
    """AI分析服务"""
    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = AIModelHandler()

    async def generate_analysis_stream_with_format(self):
        """流式生成AI分析报告，返回格式化后的HTML"""
        shipments, _ = self.shipment_dao.get_all_shipments(limit=10000)

        if not shipments:
            yield {'type': 'error', 'content': '没有可分析的数据，请先上传CSV文件'}
            return

        analysis_prompt = f"""
你是转运中心现场的班次值班经理。基于以下全量数据输出面向执行的班次简报：

数据概览：
- 总记录数: {len(shipments)}
- 状态分布: {self.model_handler._get_status_distribution(shipments)}
- 平均重量: {self.model_handler._calculate_average_weight(shipments):.2f} kg

请严格按以下结构输出（短句要点式）：
A. 今日运行态势（拥堵/异常波次/高峰时段）
B. 风险清单（TOP3：场地、车辆、干线/支线）
C. 产能与人力（分拣线利用率、缺口岗位与时段）
D. 关键KPI（SLA命中率、滞留件、问题件、装车准点）
E. 行动清单（≤5条，明确"责任岗位+完成时限"）
"""

        full_content = ""
        async for chunk in self.model_handler.generate_response_stream(analysis_prompt, ""):
            if chunk['type'] in ('thinking', 'text', 'error'):
                yield chunk
                if chunk['type'] == 'text':
                    full_content += chunk['content']

        report_html = format_ai_response(full_content)
        yield {'type': 'done', 'content': report_html}