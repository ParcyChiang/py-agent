"""饼图 - 客户类型占比"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
import random
from collections import defaultdict

from internal.pkg.utils import configure_matplotlib

_PIE_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#795548', '#FF9800', '#9C27B0']


def create_pie_chart(shipments):
    configure_matplotlib()

    max_items = 200
    if len(shipments) > max_items:
        rng = random.Random(42)
        shipments = rng.sample(shipments, max_items)

    customer_type_data = defaultdict(int)
    for shipment in shipments:
        customer_type = shipment.get('customer_type', '')
        if not customer_type or customer_type == '未知类型':
            continue
        customer_type_data[customer_type] += 1

    if not customer_type_data:
        return {'image_base64': None, 'data_info': {'error': '没有可用的数据生成饼图'}}

    sorted_data = sorted(customer_type_data.items(), key=lambda x: -x[1])
    labels = [item[0] for item in sorted_data]
    sizes = [item[1] for item in sorted_data]

    if len(labels) > 8:
        labels = labels[:7] + ['其他']
        sizes = sizes[:7] + [sum(sizes[7:])]

    fig, ax = plt.subplots(figsize=(8, 6))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=_PIE_COLORS[:len(labels)],
        autopct='%1.1f%%',
        startangle=90,
        explode=[0.02] * len(labels),
        shadow=False,
        textprops={'fontsize': 9}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)

    for text in texts:
        text.set_fontsize(9)
        text.set_color('#333333')

    ax.legend(wedges, labels, title='客户类型', loc='center left',
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)

    ax.set_title('客户类型占比分布')

    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)

    return {
        'image_base64': image_base64,
        'data_info': {'labels': labels, 'sizes': sizes}
    }
