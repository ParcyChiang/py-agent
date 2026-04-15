"""Charts module for generating 3D visualization plots.

This module provides functions to generate:
- Surface plot: city x time x status
- Scatter plot: weight x shipping_fee x city
- Wireframe plot: customer_type x priority x status
"""
from charts.surface import create_surface_plot
from charts.scatter import create_scatter_plot
from charts.wireframe import create_wireframe_plot


def generate_chart_data(shipments, daily_stats):
    """Generate 3D chart data from shipments.

    Args:
        shipments: List of shipment dictionaries
        daily_stats: Daily statistics dictionary (unused but kept for API compatibility)

    Returns:
        dict with three base64-encoded images and data_info:
        {
            'surface_3d': base64_string or None,
            'scatter_3d': base64_string or None,
            'wireframe_3d': base64_string or None,
            'data_info': {...}
        }
    """
    try:
        # Generate three types of 3D charts
        surface_result = create_surface_plot(shipments)
        scatter_result = create_scatter_plot(shipments)
        wireframe_result = create_wireframe_plot(shipments)

        # Merge data_info from all plots
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
