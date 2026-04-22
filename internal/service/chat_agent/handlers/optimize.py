# internal/service/chat_agent/handlers/optimize.py
"""优化 Handler"""
import json
from typing import Dict, List
from .base import BaseHandler, HandlerResponse


class OptimizeHandler(BaseHandler):
    """Optimize Handler - 处理物流优化请求"""

    SYSTEM_PROMPT = """你是一个物流优化专家。请分析物流数据，提出优化建议。

分析维度：
1. 路线优化：根据发货地/收货地分布，推荐更高效的集散中心布局
2. 成本优化：分析各路线的运费、重量分布，推荐更经济的快递公司组合
3. 时效优化：分析延误原因，提出改进措施

请用结构化的方式输出优化建议。"""

    async def handle(self, intent: Dict, context: List[Dict]) -> HandlerResponse:
        """处理优化请求"""
        params = intent.get('params', {})
        optimize_type = params.get('type', 'route')  # route/cost/time

        try:
            # 获取全量数据用于分析
            shipments, _ = self.dao.get_all_shipments(limit=5000)

            if not shipments:
                return HandlerResponse(
                    type='optimize',
                    content='没有足够的物流数据进行分析',
                    need_confirm=False
                )

            # 构建分析上下文
            analysis_context = self._build_analysis_context(shipments, optimize_type)

            # 调用 AI 生成优化建议
            prompt = f"优化类型：{optimize_type}\n\n数据概览：\n{analysis_context}"
            suggestions = await self._generate_suggestions(prompt)

            return HandlerResponse(
                type='optimize',
                content=suggestions,
                need_confirm=False,
                action_result=json.dumps({'optimize_type': optimize_type, 'data_count': len(shipments)})
            )
        except Exception as e:
            return HandlerResponse(
                type='optimize',
                content=f'优化分析失败: {str(e)}',
                need_confirm=False,
                error=str(e)
            )

    def _build_analysis_context(self, shipments: List[Dict], optimize_type: str) -> str:
        """构建分析上下文"""
        if optimize_type == 'route':
            routes = {}
            for s in shipments:
                key = (s.get('origin_city', ''), s.get('destination_city', ''))
                routes[key] = routes.get(key, 0) + 1
            top_routes = sorted(routes.items(), key=lambda x: x[1], reverse=True)[:10]
            context = "热门路线统计：\n"
            for (o, d), cnt in top_routes:
                context += f"- {o} → {d}: {cnt} 单\n"
            return context

        elif optimize_type == 'cost':
            companies = {}
            for s in shipments:
                c = s.get('courier_company', 'unknown')
                fee = float(s.get('shipping_fee', 0) or 0)
                if c not in companies:
                    companies[c] = {'count': 0, 'total_fee': 0}
                companies[c]['count'] += 1
                companies[c]['total_fee'] += fee

            context = "各快递公司费用统计：\n"
            for c, data in sorted(companies.items(), key=lambda x: x[1]['total_fee']/max(x[1]['count'],1)):
                avg = data['total_fee'] / max(data['count'], 1)
                context += f"- {c}: {data['count']} 单, 平均运费 {avg:.2f} 元\n"
            return context

        else:
            return f"共有 {len(shipments)} 条物流记录"

    async def _generate_suggestions(self, prompt: str) -> str:
        """调用 AI 生成优化建议"""
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n{prompt}"
        response = await self.model.generate_response_stream(full_prompt, "")

        suggestions = ""
        async for chunk in response:
            if chunk['type'] == 'text':
                suggestions += chunk['content']

        return suggestions if suggestions else "分析完成，未生成具体建议"
