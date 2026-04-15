"""图表模块 - 生成三维可视化图表

本模块提供以下功能：
- 曲面图：城市 x 时间 x 状态
- 散点图：重量 x 运费 x 城市
- 线框图：客户类型 x 优先级 x 状态
"""
from charts.surface import create_surface_plot
from charts.scatter import create_scatter_plot
from charts.wireframe import create_wireframe_plot


def generate_chart_data(shipments, daily_stats):
    """从物流数据生成三维图表数据

    参数:
        shipments: 物流数据字典列表
        daily_stats: 每日统计字典（未使用，保留以兼容 API）

    返回:
        包含三个 base64 编码图片和 data_info 的字典:
        {
            'surface_3d': base64字符串或None,
            'scatter_3d': base64字符串或None,
            'wireframe_3d': base64字符串或None,
            'data_info': {...}
        }
    """
    try:
        # 生成三种类型的三维图
        surface_result = create_surface_plot(shipments)
        scatter_result = create_scatter_plot(shipments)
        wireframe_result = create_wireframe_plot(shipments)

        # 合并所有图表的 data_info
        data_info = {}
        data_info.update(surface_result.get('data_info', {}))
        data_info.update(scatter_result.get('data_info', {}))
        data_info.update(wireframe_result.get('data_info', {}))

        return {
            'surface_3d': surface_result.get('image_base64'),
            'scatter_3d': scatter_result.get('image_base64'),
            'wireframe_3d': wireframe_result.get('image_base64'),
            'data_info': data_info
        }
    except Exception as e:
        print(f"生成三维图时出错: {e}")
        return {
            'surface_3d': None,
            'scatter_3d': None,
            'wireframe_3d': None,
            'data_info': {
                'error': str(e)
            }
        }


__all__ = ['generate_chart_data', 'create_surface_plot', 'create_scatter_plot', 'create_wireframe_plot']
