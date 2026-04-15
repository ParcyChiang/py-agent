"""3D Scatter plot for weight x shipping_fee x city"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
from mpl_toolkits.mplot3d import Axes3D

from utils import configure_matplotlib


def create_scatter_plot(shipments):
    """Generate 3D scatter plot data: weight x shipping_fee x city distribution.

    Args:
        shipments: List of shipment dictionaries

    Returns:
        dict with 'image_base64' and 'data_info' keys
    """
    configure_matplotlib()

    # Prepare scatter data: weight x shipping_fee x city
    weight_fee_city_data = []

    for shipment in shipments:
        weight = shipment.get('weight', 0)
        shipping_fee = shipment.get('shipping_fee', 0)
        city = shipment.get('origin_city', '未知城市')
        if weight > 0 and shipping_fee > 0 and city != '未知城市':
            weight_fee_city_data.append({
                'weight': weight,
                'shipping_fee': shipping_fee,
                'city': city
            })

    # Debug info
    print(f"散点图数据点数量: {len(weight_fee_city_data)}")

    if not weight_fee_city_data:
        return {
            'image_base64': None,
            'data_info': {
                'scatter_info': {
                    'weight_range': [],
                    'fee_range': [],
                    'cities': []
                },
                'error': '没有可用的数据生成散点图'
            }
        }

    # Scatter plot data preparation
    unique_cities = sorted(list(set(item['city'] for item in weight_fee_city_data)))
    city_to_index = {city: i for i, city in enumerate(unique_cities)}

    # Generate 3D scatter plot - dimensions: weight x shipping_fee x city
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Assign colors to different cities
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
    city_colors = {city: colors[i % len(colors)] for i, city in enumerate(unique_cities)}

    # Draw scatter plot
    for item in weight_fee_city_data:
        weight = item['weight']
        shipping_fee = item['shipping_fee']
        city_idx = city_to_index[item['city']]
        color = city_colors[item['city']]

        ax.scatter(weight, shipping_fee, city_idx, c=color,
                 label=item['city'] if city_idx == 0 else "", s=50, alpha=0.7)

    # Show only unique city labels
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    ax.set_xlabel('重量 (kg)')
    ax.set_ylabel('运费 (元)')
    ax.set_zlabel('城市')
    ax.set_title('三维散点图 - 重量x运费x城市分布')

    # Set z-axis labels
    ax.set_zticks(range(len(unique_cities)))
    ax.set_zticklabels(unique_cities)

    plt.tight_layout()

    # Convert to base64 string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()

    return {
        'image_base64': image_base64,
        'data_info': {
            'scatter_info': {
                'weight_range': [min(item['weight'] for item in weight_fee_city_data), max(item['weight'] for item in weight_fee_city_data)],
                'fee_range': [min(item['shipping_fee'] for item in weight_fee_city_data), max(item['shipping_fee'] for item in weight_fee_city_data)],
                'cities': unique_cities
            }
        }
    }
