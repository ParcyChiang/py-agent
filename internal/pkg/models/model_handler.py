# internal/models/model_handler.py
"""AI 模型处理器"""
import os
import asyncio
import logging
import requests

logger = logging.getLogger("LogisticsAgent")


class AIResponse:
    """AI 响应封装，可当字符串使用，同时保留 thinking 内容"""

    def __init__(self, text: str, thinking: str = ""):
        self.text = text
        self.thinking = thinking

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"AIResponse(text={self.text[:50]}..., thinking={self.thinking[:50]}...)" if self.thinking else f"AIResponse(text={self.text[:50]}...)"


def create_model_handler(model_name: str = "MiniMax-M2.7-highspeed"):
    """创建模型处理器，默认使用MiniMax API"""
    api_key = os.getenv("MINIMAX_API_KEY")
    if api_key:
        return AIModelHandler(model_name, api_key)
    raise ValueError("未配置AI_API_KEY")


class AIModelHandler:
    """AI API模型处理器"""

    def __init__(self, model_name: str = "MiniMax-M2.7-highspeed", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.api_url = os.getenv("MINIMAX_API_URL", "https://api.minimaxi.com/anthropic/v1/messages")

    async def generate_response(self, prompt: str, context: str = "") -> AIResponse:
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
                    thinking_parts = []
                    for item in content:
                        item_type = item.get("type", "")
                        if item_type == "text":
                            text_parts.append(item.get("text", ""))
                        elif item_type == "thinking":
                            thinking_parts.append(item.get("thinking", ""))
                    text = "\n".join(text_parts) if text_parts else str(content)
                    thinking = "\n".join(thinking_parts)
                    return AIResponse(text, thinking)
                elif isinstance(content, str):
                    return AIResponse(content, "")
            logger.error(f"API响应格式异常: {result}")
            return AIResponse("抱歉，模型返回格式异常", "")

        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            return AIResponse("抱歉，模型请求超时，请稍后重试", "")
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return AIResponse(f"抱歉，模型调用失败: {str(e)}", "")
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return AIResponse(f"抱歉，处理您的请求时出现错误: {str(e)}", "")

    async def generate_response_stream(self, prompt: str, context: str = ""):
        """使用API生成响应，真正的流式返回thinking和text"""
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
                "max_tokens": 4096,
                "stream": True  # 启用流式响应
            }

            # 使用 stream=True 进行真正的流式请求
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120, stream=True)
            response.raise_for_status()

            logger.info("开始流式接收响应...")

            # 逐行读取 SSE 响应
            for line in response.iter_lines():
                if not line:
                    continue

                line_text = line.decode('utf-8')

                # SSE 格式: data: {...}
                if line_text.startswith('data: '):
                    data_str = line_text[6:].strip()

                    # 跳过 [DONE] 标记
                    if data_str == '[DONE]':
                        break

                    try:
                        import json as json_module
                        data = json_module.loads(data_str)

                        # 处理不同类型的事件
                        event_type = data.get("type", "")

                        if event_type == "content_block_start":
                            # 内容块开始，可能是 thinking 或 text
                            content_block = data.get("content_block", {})
                            block_type = content_block.get("type", "")
                            if block_type == "thinking":
                                yield {"type": "thinking", "content": ""}
                            elif block_type == "text":
                                yield {"type": "text", "content": ""}

                        elif event_type == "content_block_delta":
                            # 内容块增量更新
                            delta = data.get("delta", {})
                            delta_type = delta.get("type", "")

                            if delta_type == "thinking_delta":
                                content = delta.get("thinking", "")
                                if content:
                                    yield {"type": "thinking", "content": content}
                            elif delta_type == "text_delta":
                                content = delta.get("text", "")
                                if content:
                                    yield {"type": "text", "content": content}
                            elif delta_type == "signature_delta":
                                # 签名块，忽略
                                pass

                        elif event_type == "message_delta":
                            # 消息完成
                            delta = data.get("delta", {})
                            if delta.get("stop_reason") == "end_turn":
                                logger.info("流式响应完成")
                                break

                    except json_module.JSONDecodeError:
                        # 忽略无法解析的行
                        pass

        except requests.exceptions.Timeout:
            logger.error("API请求超时")
            yield {"type": "error", "content": "抱歉，模型请求超时，请稍后重试"}
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            yield {"type": "error", "content": f"抱歉，模型调用失败: {str(e)}"}
        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            yield {"type": "error", "content": f"抱歉，处理您的请求时出现错误: {str(e)}"}

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
