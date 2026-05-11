# internal/service/chat_agent/handlers/mutation.py
"""增删改 Handler"""
import json
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class MutationHandler(BaseHandler):
    """Mutation Handler - 处理数据增删改请求"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理写操作请求"""
        params = intent.get('params', {})
        action = params.get('action')  # update/delete/insert
        filters = params.get('filters', {})
        updates = params.get('updates', {})

        try:
            if action == 'update':
                return await self._handle_update(intent, filters, updates)
            elif action == 'delete':
                return await self._handle_delete(intent, filters)
            else:
                return HandlerResponse(
                    type='mutation',
                    content=f'不支持的操作类型: {action}',
                    need_confirm=False,
                    error=f'Unknown action: {action}'
                )
        except Exception as e:
            return HandlerResponse(
                type='mutation',
                content=f'操作失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    async def _handle_update(self, intent: Dict, filters: Dict, updates: Dict) -> HandlerResponse:
        """处理更新操作 - 返回行动计划，等待确认"""
        # 构造 SQL 条件
        conditions = []
        params_list = []
        if 'status' in filters:
            conditions.append("status = %s")
            params_list.append(filters['status'])
        if 'days' in filters:
            conditions.append(f"created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)")
            params_list.append(filters['days'])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with self.dao.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT id, status FROM shipments WHERE {where_clause} LIMIT 100",
                    params_list
                )
                affected = cursor.fetchall()

        if not affected:
            return HandlerResponse(
                type='mutation',
                content='未找到需要更新的记录',
                need_confirm=False
            )

        affected_ids = [r['id'] for r in affected]
        affected_count = len(affected_ids)

        # 构造行动计划
        new_status = updates.get('status', '')
        plan = {
            'action': 'update',
            'filters': filters,
            'updates': updates,
            'affected_ids': affected_ids,
            'affected_count': affected_count,
            'description': f"将 {affected_count} 条记录的状态更新为 '{new_status}'"
        }

        plan_text = f"我计划执行以下操作：\n"
        plan_text += f"1. 根据条件筛选出 {affected_count} 条物流记录\n"
        plan_text += f"2. 将它们的状态更新为 '{new_status}'\n"
        plan_text += f"\n是否确认执行？"

        return HandlerResponse(
            type='mutation',
            content=plan_text,
            need_confirm=True,
            action_plan=plan
        )

    async def _handle_delete(self, intent: Dict, filters: Dict) -> HandlerResponse:
        """处理删除操作"""
        return HandlerResponse(
            type='mutation',
            content='删除操作暂未实现',
            need_confirm=False,
            error='Delete not implemented'
        )

    async def handle_stream(self, intent: Dict, context: List[Dict]):
        """流式处理写操作请求"""
        params = intent.get('params', {})
        action = params.get('action')  # update/delete/insert

        try:
            if action == 'update':
                # 流式返回更新计划
                plan_response = await self._handle_update(intent, params.get('filters', {}), params.get('updates', {}))
                # 分段 yield 计划文本
                for i in range(0, len(plan_response.content), 50):
                    yield {'type': 'text', 'content': plan_response.content[i:i+50]}
                if plan_response.need_confirm:
                    yield {'type': 'need_confirm', 'action_plan': plan_response.action_plan}
            elif action == 'delete':
                yield {'type': 'text', 'content': '删除操作暂未实现'}
            else:
                yield {'type': 'error', 'content': f'不支持的操作类型: {action}'}
        except Exception as e:
            yield {'type': 'error', 'content': f'操作失败: {str(e)}'}

    async def execute_update(self, plan: Dict) -> HandlerResponse:
        """执行更新 - Diff 确认后调用"""
        try:
            affected_ids = plan.get('affected_ids', [])
            new_status = plan.get('updates', {}).get('status')

            if not affected_ids or not new_status:
                return HandlerResponse(
                    type='mutation',
                    content='参数错误',
                    need_confirm=False,
                    error='Missing parameters'
                )

            count, before, after = self.dao.batch_update_status(affected_ids, new_status)

            return HandlerResponse(
                type='mutation',
                content=f'成功更新 {count} 条记录',
                need_confirm=False,
                diff={'before': before, 'after': after},
                action_result=json.dumps({'affected_rows': count})
            )
        except Exception as e:
            return HandlerResponse(
                type='mutation',
                content=f'更新失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )
