"""3D Wireframe plot for customer_type x priority x status"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
from mpl_toolkits.mplot3d import Axes3D
from collections import defaultdict

from constants import STATUS_CN_MAP
from utils import configure_matplotlib


def create_wireframe_plot(shipments):
    """Generate 3D wireframe plot data: customer_type x priority x status distribution.

    Args:
        shipments: List of shipment dictionaries

    Returns:
        dict with 'image_base64' and 'data_info' keys
    """
    configure_matplotlib()

    # Prepare wireframe data: customer_type x priority x status
    customer_priority_status_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for shipment in shipments:
        # Convert status to Chinese
        status = shipment.get('status', '未知状态')
        status_cn = STATUS_CN_MAP.get(status, status)

        # Process wireframe data
        customer_type = shipment.get('customer_type', '未知类型')
        priority = shipment.get('priority', '未知优先级')
        if customer_type != '未知类型' and priority != '未知优先级' and status_cn != '未知状态':
            customer_priority_status_data[customer_type][priority][status_cn] += 1

    # Debug info
    print(f"线框图数据点数量: {sum(sum(sum(status_data.values()) for status_data in priority_data.values()) for priority_data in customer_priority_status_data.values())}")

    if not customer_priority_status_data:
        return {
            'image_base64': None,
            'data_info': {
                'wireframe_info': {
                    'customer_types': [],
                    'priorities': [],
                    'statuses': []
                },
                'error': '没有可用的数据生成线框图'
            }
        }

    # Wireframe data preparation
    all_customer_types = sorted(list(customer_priority_status_data.keys()))
    all_priorities = sorted(list(set(priority for priority_data in customer_priority_status_data.values() for priority in priority_data.keys())))
    all_line_statuses = sorted(list(set(status for priority_data in customer_priority_status_data.values() for status_data in priority_data.values() for status in status_data.keys())))

    # Create wireframe plot data matrix
    X_wireframe = np.arange(len(all_customer_types))  # Customer type indices
    Y_wireframe = np.arange(len(all_priorities))  # Priority indices
    X_wireframe, Y_wireframe = np.meshgrid(X_wireframe, Y_wireframe)

    wireframe_data = {}
    for status in all_line_statuses:
        Z = np.zeros((len(all_priorities), len(all_customer_types)))
        for i, priority in enumerate(all_priorities):
            for j, customer_type in enumerate(all_customer_types):
                Z[i, j] = customer_priority_status_data.get(customer_type, {}).get(priority, {}).get(status, 0)
        wireframe_data[status] = Z

    # Generate 3D wireframe plot - dimensions: customer_type x priority x status
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']

    for i, (status, Z) in enumerate(wireframe_data.items()):
        if i < len(colors):
            ax.plot_wireframe(X_wireframe, Y_wireframe, Z, color=colors[i], alpha=0.8,
                            linewidth=1, label=status)

    ax.set_xlabel('客户类型')
    ax.set_ylabel('优先级')
    ax.set_zlabel('数量')
    ax.set_title('三维线框图 - 客户类型x优先级x状态分布')

    # Set axis labels
    ax.set_xticks(range(len(all_customer_types)))
    ax.set_xticklabels(all_customer_types, rotation=45)
    ax.set_yticks(range(len(all_priorities)))
    ax.set_yticklabels(all_priorities)

    ax.legend()
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
            'wireframe_info': {
                'customer_types': all_customer_types,
                'priorities': all_priorities,
                'statuses': all_line_statuses
            }
        }
    }
