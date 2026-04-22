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