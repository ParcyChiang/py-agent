# internal/service/chat_agent/handlers/query.py
"""查询 Handler"""
import json
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class QueryHandler(BaseHandler):
    """查询 Handler - 处理数据查询请求"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理查询请求"""
        params = intent.get('params', {})
        status = params.get('status')
        days = params.get('days')
        origin = params.get('origin')
        destination = params.get('destination')

        try:
            shipments = self.dao.get_shipments_by_criteria(
                status=status,
                days=days,
                origin=origin,
                destination=destination
            )

            if not shipments:
                return HandlerResponse(
                    type='query',
                    content='未找到符合条件的物流记录',
                    need_confirm=False
                )

            # 生成统计摘要
            total = len(shipments)
            status_dist = {}
            for s in shipments:
                st = s.get('status', 'unknown')
                status_dist[st] = status_dist.get(st, 0) + 1

            summary = f"共找到 {total} 条物流记录：\n"
            for st, cnt in status_dist.items():
                summary += f"- {st}: {cnt} 条\n"

            # 如果记录不多，显示详细信息
            if total <= 20:
                summary += "\n详细信息：\n"
                for s in shipments[:20]:
                    summary += f"[{s['id']}] {s['origin']} → {s['destination']} | 状态: {s['status']}\n"

            return HandlerResponse(
                type='query',
                content=summary,
                need_confirm=False,
                action_result=json.dumps({'count': total, 'status_distribution': status_dist})
            )
        except Exception as e:
            return HandlerResponse(
                type='query',
                content=f'查询失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    async def handle_stream(self, intent: Dict, context: List[Dict]):
        """流式处理查询请求"""
        params = intent.get('params', {})
        status = params.get('status')
        days = params.get('days')
        origin = params.get('origin')
        destination = params.get('destination')

        try:
            shipments = self.dao.get_shipments_by_criteria(
                status=status,
                days=days,
                origin=origin,
                destination=destination
            )

            if not shipments:
                yield {'type': 'text', 'content': '未找到符合条件的物流记录'}
                return

            # 生成统计摘要
            total = len(shipments)
            status_dist = {}
            for s in shipments:
                st = s.get('status', 'unknown')
                status_dist[st] = status_dist.get(st, 0) + 1

            summary = f"共找到 {total} 条物流记录：\n"
            for st, cnt in status_dist.items():
                summary += f"- {st}: {cnt} 条\n"

            # 分段 yield
            for i in range(0, len(summary), 50):
                yield {'type': 'text', 'content': summary[i:i+50]}

            # 如果记录不多，显示详细信息
            if total <= 20:
                detail_header = "\n详细信息：\n"
                for i in range(0, len(detail_header), 50):
                    yield {'type': 'text', 'content': detail_header[i:i+50]}

                for s in shipments[:20]:
                    detail_line = f"[{s['id']}] {s['origin']} → {s['destination']} | 状态: {s['status']}\n"
                    for i in range(0, len(detail_line), 50):
                        yield {'type': 'text', 'content': detail_line[i:i+50]}

        except Exception as e:
            yield {'type': 'error', 'content': f'查询失败: {str(e)}'}
