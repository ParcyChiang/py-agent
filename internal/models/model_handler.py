# internal/models/model_handler.py
"""AI 模型处理器"""
import os
import logging
import requests

logger = logging.getLogger("LogisticsAgent")


def create_model_handler(model_name: str = "MiniMax-M2.7-highspeed"):
    """创建模型处理器，默认使用MiniMax API"""
    api_key = os.getenv("MINIMAX_API_KEY")
    if api_key:
        return MiniMaxModelHandler(model_name, api_key)
    raise ValueError("未配置MINIMAX_API_KEY")


class MiniMaxModelHandler:
    """MiniMax API模型处理器"""

    def __init__(self, model_name: str = "MiniMax-M2.7-highspeed", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.api_url = os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/anthropic/v1/messages")

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """使用API生成响应"""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "user", "content": full_prompt}
                ],
                "max_tokens": 4096
            }

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            logger.info(f"API响应: {result}")
            if "content" in result:
                content = result["content"]
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        item_type = item.get("type", "")
                        if item_type == "text":
                            text_parts.append(item.get("text", ""))
                        elif item_type == "thinking":
                            logger.info("跳过thinking内容")
                    return "\n".join(text_parts) if text_parts else str(content)
                elif isinstance(content, str):
                    return content
            logger.error(f"API响应格式异常: {result}")
            return f"抱歉，模型返回格式异常"

        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return "抱歉，模型请求超时，请稍后重试"
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return f"抱歉，模型调用失败: {str(e)}"
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    async def analyze_shipment_data(self, shipment_data):
        """分析物流数据"""
        prompt = f"""
        你是一个大型分拨中心的运营分析员。基于以下货件信息，按物流中心的现实业务给出可执行洞察：
        {self._format_shipment_data(shipment_data)}

        输出用简洁要点（每点≤20字），包含：
        1) 运营状态：是否异常、阻塞位置
        2) 风险预警：延误/错分/逆向等（概率+影响）
        3) 优先动作：今天需跟进的2-3个动作（含岗位）
        4) SLA 提醒：是否命中SLA阈值（建议缓解措施）
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    async def analyze_bulk_data(self, shipments_data):
        """批量分析物流数据"""
        prompt = f"""
        你是转运中心现场的班次值班经理。基于以下全量数据输出面向执行的班次简报：

        数据概览：
        - 总记录数: {len(shipments_data)}
        - 状态分布: {self._get_status_distribution(shipments_data)}
        - 平均重量: {self._calculate_average_weight(shipments_data):.2f} kg

        请严格按以下结构输出（短句要点式）：
        A. 今日运行态势（拥堵/异常波次/高峰时段）
        B. 风险清单（TOP3：场地、车辆、干线/支线）
        C. 产能与人力（分拣线利用率、缺口岗位与时段）
        D. 关键KPI（SLA命中率、滞留件、问题件、装车准点）
        E. 行动清单（≤5条，明确"责任岗位+完成时限"）
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "summary": {
                "total_records": len(shipments_data),
                "status_distribution": self._get_status_distribution(shipments_data),
                "average_weight": self._calculate_average_weight(shipments_data)
            }
        }

    async def predict_delivery_time(self, shipment_data, historical_data=None):
        """预测交付时间"""
        context = "历史数据预测" if historical_data else "当前数据预测"

        prompt = f"""
        {context}

        当前货物：{shipment_data.get('id')}，{shipment_data.get('origin')}→{shipment_data.get('destination')}
        状态：{shipment_data.get('status')}，重量：{shipment_data.get('weight')}kg

        请预测交付时间（格式：X天，置信度：X%）
        """

        prediction = await self.generate_response(prompt)
        return {
            "prediction": prediction,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }

    async def generate_daily_report(self, daily_stats, shipments_data):
        """生成每日报告"""
        prompt = f"""
        生成每日日报（面向管理层的一页纸）：

        核心统计：发货{daily_stats.get('total_shipments', 0)}，交付{daily_stats.get('delivered', 0)}，
                 延迟{daily_stats.get('delayed', 0)}，准时率{daily_stats.get('on_time_rate', 0):.1f}%

        输出模块：
        1) 经营看板：SLA、吞吐、滞留走势（一句话趋势）
        2) 异常焦点：TOP2异常及影响（金额/客户/区域）
        3) 纠偏措施：已执行与待执行（负责人+截止时间）
        4) 明日安排：人车资源与产能计划（风险点）
        """

        report = await self.generate_response(prompt)
        return {
            "date": daily_stats.get('date'),
            "report": report,
            "statistics": daily_stats
        }

    def _get_status_distribution(self, shipments_data):
        """获取状态分布"""
        from internal.pkg.constants import STATUS_CN_MAP
        distribution = {}
        for shipment in shipments_data:
            status = shipment.get('status', 'unknown')
            cn_status = STATUS_CN_MAP.get(status, status)
            distribution[cn_status] = distribution.get(cn_status, 0) + 1
        return distribution

    def _calculate_average_weight(self, shipments_data):
        """计算平均重量"""
        if not shipments_data:
            return 0.0
        total_weight = sum(shipment.get('weight', 0) for shipment in shipments_data)
        return total_weight / len(shipments_data)

    def _format_shipment_data(self, shipment_data):
        """格式化单个物流数据"""
        return f"""
        物流单号: {shipment_data.get('id')}
        状态: {shipment_data.get('status')}
        发货地: {shipment_data.get('origin')} ({shipment_data.get('origin_city')})
        收货地: {shipment_data.get('destination')} ({shipment_data.get('destination_city')})
        快递公司: {shipment_data.get('courier_company')}
        重量: {shipment_data.get('weight')} kg
        运费: {shipment_data.get('shipping_fee')} 元
        创建时间: {shipment_data.get('created_at')}
        预计送达: {shipment_data.get('estimated_delivery')}
        实际送达: {shipment_data.get('actual_delivery')}
        """
