"""热力图 - 城市 x 状态的分布密度"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import io
import random
from collections import defaultdict

from internal.pkg.constants import STATUS_CN_MAP
from internal.pkg.utils import configure_matplotlib

_HEATMAP_CMAP = 'YlOrRd'


def create_heatmap_plot(shipments):
    configure_matplotlib()

    max_items = 200
    if len(shipments) > max_items:
        rng = random.Random(42)
        shipments = rng.sample(shipments, max_items)

    city_status_data = defaultdict(lambda: defaultdict(int))

    for shipment in shipments:
        status = shipment.get('status', '')
        status_cn = STATUS_CN_MAP.get(status, status)
        if not status_cn or status_cn == '未知状态':
            continue

        city = shipment.get('origin_city', '')
        if not city or city == '未知城市':
            continue

        city_status_data[city][status_cn] += 1

    if not city_status_data:
        return {'image_base64': None, 'data_info': {'error': '没有可用的数据生成热力图'}}

    cities = sorted(city_status_data.keys())
    all_statuses = sorted(set(
        status for status_dict in city_status_data.values()
        for status in status_dict.keys()
    ))

    if not cities or not all_statuses:
        return {'image_base64': None, 'data_info': {'error': '数据维度不足，无法生成热力图'}}

    matrix = np.zeros((len(cities), len(all_statuses)))
    for i, city in enumerate(cities):
        for j, status in enumerate(all_statuses):
            matrix[i, j] = city_status_data[city][status]

    fig, ax = plt.subplots(figsize=(10, max(6, len(cities) * 0.6)))
    sns.heatmap(
        matrix,
        xticklabels=all_statuses,
        yticklabels=cities,
        cmap=_HEATMAP_CMAP,
        annot=True,
        fmt='.0f',
        linewidths=0.5,
        linecolor='white',
        cbar_kws={'label': '数量', 'shrink': 0.8},
        ax=ax
    )

    ax.set_xlabel('物流状态')
    ax.set_ylabel('城市')
    ax.set_title('城市 x 状态 分布热力图')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha='right', fontsize=9)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)

    return {
        'image_base64': image_base64,
        'data_info': {
            'cities': cities,
            'statuses': all_statuses,
            'matrix': matrix.tolist()
        }
    }
