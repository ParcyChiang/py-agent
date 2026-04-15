"""3D Surface plot for city x time x status"""
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
from charts.utils import _parse_date_str


def create_surface_plot(shipments):
    """Generate 3D surface plot data: city x time x status distribution.

    Args:
        shipments: List of shipment dictionaries

    Returns:
        dict with 'image_base64' and 'data_info' keys
    """
    configure_matplotlib()

    # Debug info
    print(f"收到 {len(shipments)} 条物流数据")
    if shipments:
        print(f"第一条数据字段: {list(shipments[0].keys())}")
        print(f"第一条数据示例: {shipments[0]}")

    # Prepare surface data: time x city x status
    time_city_status_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for shipment in shipments:
        # Convert status to Chinese
        status = shipment.get('status', '未知状态')
        status_cn = STATUS_CN_MAP.get(status, status)

        # Process surface data
        delivery_date = _parse_date_str(shipment.get('actual_delivery'))
        if delivery_date is None:
            delivery_date = _parse_date_str(shipment.get('created_at'))

        if delivery_date is not None:
            city = shipment.get('origin_city', '未知城市')
            if city and city != '未知城市' and status_cn and status_cn != '未知状态':
                time_city_status_data[delivery_date][city][status_cn] += 1

    # Debug info
    print(f"曲面图数据点数量: {sum(sum(sum(city_data.values()) for city_data in day_data.values()) for day_data in time_city_status_data.values())}")

    # Get data range
    if not time_city_status_data:
        return {
            'image_base64': None,
            'data_info': {
                'cities': [],
                'time_labels': [],
                'statuses': [],
                'error': '没有可用的数据生成三维图表'
            }
        }

    # Get all dates and sort (surface)
    all_dates = sorted(time_city_status_data.keys())
    if len(all_dates) > 7:
        # If data exceeds 7 days, take the last 7 days
        last_7_days = all_dates[-7:]
    else:
        # If data less than 7 days, use all available dates
        last_7_days = all_dates

    # Define all possible statuses
    all_possible_statuses = [
        '已送达', '配送失败', '运输中', '派件中',
        '待处理', '已揽件', '处理中', '已退回'
    ]

    # Surface data preparation
    all_cities = set()
    all_statuses = set()
    for day_data in time_city_status_data.values():
        for city in day_data.keys():
            all_cities.add(city)
            for status in day_data[city].keys():
                all_statuses.add(status)

    # Merge all possible statuses
    for status in all_possible_statuses:
        all_statuses.add(status)

    all_cities = sorted(list(all_cities))[:8]  # Limit to first 8 cities
    all_statuses = sorted(list(all_statuses))  # Allow all statuses

    # Create surface plot data matrix
    X_surface = np.arange(len(all_cities))  # City indices
    Y_surface = np.arange(len(last_7_days))  # Time indices
    X_surface, Y_surface = np.meshgrid(X_surface, Y_surface)

    # Create Z value matrix for each status (surface)
    surface_data = {}
    for status in all_statuses:
        Z = np.zeros((len(last_7_days), len(all_cities)))
        for i, day in enumerate(last_7_days):
            for j, city in enumerate(all_cities):
                Z[i, j] = time_city_status_data[day][city][status]
        surface_data[status] = Z

    # Generate 3D surface plot - dimensions: city x time x status count
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']

    for i, (status, Z) in enumerate(surface_data.items()):
        if i < len(colors):
            surf = ax.plot_surface(X_surface, Y_surface, Z, alpha=0.7, color=colors[i],
                                 label=status, linewidth=0, antialiased=True)

    ax.set_xlabel('城市')
    ax.set_ylabel('时间')
    ax.set_zlabel('数量')
    ax.set_title('三维曲面图 - 城市x时间x状态分布')

    # Set axis labels
    ax.set_xticks(range(len(all_cities)))
    ax.set_xticklabels(all_cities, rotation=45)
    ax.set_yticks(range(len(last_7_days)))
    ax.set_yticklabels([d.strftime('%m-%d') for d in last_7_days])

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
            'cities': all_cities,
            'time_labels': [d.strftime('%m-%d') for d in last_7_days],
            'statuses': all_statuses,
            'surface_data': {k: v.tolist() for k, v in surface_data.items()}
        }
    }
