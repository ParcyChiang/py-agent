"""图表模块 - 生成三维可视化图表

本模块提供以下功能：
- 曲面图：城市 x 时间 x 状态
- 散点图：重量 x 运费 x 城市
- 线框图：客户类型 x 优先级 x 状态
- 热力图：城市 x 状态分布
- 柱状图：每日发货量统计
- 折线图：时间趋势分析
- 饼图：客户类型占比
"""
from internal.pkg.charts.surface import create_surface_plot
from internal.pkg.charts.scatter import create_scatter_plot
from internal.pkg.charts.wireframe import create_wireframe_plot
from internal.pkg.charts.heatmap import create_heatmap_plot
from internal.pkg.charts.bar import create_bar_chart
from internal.pkg.charts.line import create_line_chart
from internal.pkg.charts.pie import create_pie_chart


def generate_chart_data(shipments, daily_stats):
    """从物流数据生成三维图表数据

    参数:
        shipments: 物流数据字典列表
        daily_stats: 每日统计字典（未使用，保留以兼容 API）

    返回:
        包含 base64 编码图片和 data_info 的字典
    """
    try:
        surface_result = create_surface_plot(shipments)
        scatter_result = create_scatter_plot(shipments)
        wireframe_result = create_wireframe_plot(shipments)
        heatmap_result = create_heatmap_plot(shipments)
        bar_result = create_bar_chart(shipments)
        line_result = create_line_chart(shipments)
        pie_result = create_pie_chart(shipments)

        data_info = {}
        data_info.update(surface_result.get('data_info', {}))
        data_info.update(scatter_result.get('data_info', {}))
        data_info.update(wireframe_result.get('data_info', {}))
        data_info.update(heatmap_result.get('data_info', {}))
        data_info.update(bar_result.get('data_info', {}))
        data_info.update(line_result.get('data_info', {}))
        data_info.update(pie_result.get('data_info', {}))

        return {
            'surface_3d': surface_result.get('image_base64'),
            'scatter_3d': scatter_result.get('image_base64'),
            'wireframe_3d': wireframe_result.get('image_base64'),
            'heatmap': heatmap_result.get('image_base64'),
            'bar_chart': bar_result.get('image_base64'),
            'line_chart': line_result.get('image_base64'),
            'pie_chart': pie_result.get('image_base64'),
            'data_info': data_info
        }
    except Exception as e:
        print(f"生成图表时出错: {e}")
        return {
            'surface_3d': None,
            'scatter_3d': None,
            'wireframe_3d': None,
            'heatmap': None,
            'bar_chart': None,
            'line_chart': None,
            'pie_chart': None,
            'data_info': {'error': str(e)}
        }


__all__ = [
    'generate_chart_data',
    'create_surface_plot',
    'create_scatter_plot',
    'create_wireframe_plot',
    'create_heatmap_plot',
    'create_bar_chart',
    'create_line_chart',
    'create_pie_chart',
]
