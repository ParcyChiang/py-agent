#模型处理类
import ollama
import logging
from datetime import datetime
from typing import Dict, List, Any
import asyncio

logger = logging.getLogger("LogisticsAgent")


class OllamaModelHandler:
    """Ollama模型处理器"""

    def __init__(self, model_name: str = "gpy-oss:20b"):
        self.model_name = model_name

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """使用Ollama生成响应"""
        try:
            # 构建完整的提示词
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': full_prompt}]
            )

            return response['message']['content']

        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    async def analyze_shipment_data(self, shipment_data: Dict) -> Dict:
        """分析物流数据"""
        prompt = f"""
        请分析以下物流数据并提供见解：
        {self._format_shipment_data(shipment_data)}

        请提供：
        1. 当前状态分析
        2. 预计交付时间的准确性评估
        3. 任何潜在问题或延迟的风险
        4. 优化建议
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    async def analyze_bulk_data(self, shipments_data: List[Dict]) -> Dict:
        """批量分析物流数据"""
        prompt = f"""
        请分析以下物流数据集并提供整体见解：

        数据概览：
        - 总记录数: {len(shipments_data)}
        - 状态分布: {self._get_status_distribution(shipments_data)}
        - 平均重量: {self._calculate_average_weight(shipments_data):.2f} kg

        请提供：
        1. 整体运营状况分析
        2. 效率评估和改进建议
        3. 潜在风险点和应对策略
        4. 客户服务优化建议
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_records": len(shipments_data),
                "status_distribution": self._get_status_distribution(shipments_data),
                "average_weight": self._calculate_average_weight(shipments_data)
            }
        }

    async def predict_delivery_time(self, shipment_data: Dict, historical_data: List[Dict] = None) -> Dict:
        """预测交付时间"""
        context = "基于历史物流数据预测交付时间" if historical_data else "基于当前物流数据预测交付时间"

        prompt = f"""
        {context}

        当前物流数据：
        {self._format_shipment_data(shipment_data)}

        {f'历史数据示例: {json.dumps(historical_data[:3], indent=2)}' if historical_data else ''}

        请预测最可能的交付时间，并给出置信度评估。
        """

        prediction = await self.generate_response(prompt)
        return {
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }

    async def generate_daily_report(self, daily_stats: Dict, shipments_data: List[Dict]) -> Dict:
        """生成每日报告"""
        prompt = f"""
        根据以下物流数据生成每日报告：

        每日统计:
        - 总发货量: {daily_stats.get('total_shipments', 0)}
        - 已交付: {daily_stats.get('delivered', 0)}
        - 延迟交付: {daily_stats.get('delayed', 0)}
        - 准时率: {daily_stats.get('on_time_rate', 0):.2f}%

        数据样本:
        {self._format_sample_shipments(shipments_data[:5])}

        请提供：
        1. 当日物流概况总结
        2. 关键指标分析和解读
        3. 异常情况和高风险货物提醒
        4. 改进建议和优化策略
        """

        report = await self.generate_response(prompt)

        return {
            "date": daily_stats.get('date'),
            "report": report,
            "statistics": daily_stats
        }

    def _format_shipment_data(self, shipment_data: Dict) -> str:
        """格式化物流数据用于提示词"""
        return f"""
        物流ID: {shipment_data.get('id')}
        起始地: {shipment_data.get('origin')}
        目的地: {shipment_data.get('destination')}
        状态: {shipment_data.get('status')}
        预计交付: {shipment_data.get('estimated_delivery')}
        实际交付: {shipment_data.get('actual_delivery')}
        重量: {shipment_data.get('weight')} kg
        尺寸: {shipment_data.get('dimensions', {})}
        客户ID: {shipment_data.get('customer_id')}
        """

    def _get_status_distribution(self, shipments_data: List[Dict]) -> Dict[str, int]:
        """获取状态分布"""
        distribution = {}
        for shipment in shipments_data:
            status = shipment.get('status', 'unknown')
            distribution[status] = distribution.get(status, 0) + 1
        return distribution

    def _calculate_average_weight(self, shipments_data: List[Dict]) -> float:
        """计算平均重量"""
        if not shipments_data:
            return 0.0

        total_weight = sum(shipment.get('weight', 0) for shipment in shipments_data)
        return total_weight / len(shipments_data)

    def _format_sample_shipments(self, shipments_data: List[Dict]) -> str:
        """格式化样本数据用于提示词"""
        if not shipments_data:
            return "无数据"

        result = ""
        for i, shipment in enumerate(shipments_data, 1):
            result += f"{i}. ID: {shipment.get('id')}, 状态: {shipment.get('status')}, " \
                      f"从 {shipment.get('origin')} 到 {shipment.get('destination')}\n"

        return result