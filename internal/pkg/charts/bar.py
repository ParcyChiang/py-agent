"""柱状图 - 每日发货量统计"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
import random
from collections import defaultdict

from internal.pkg.utils import configure_matplotlib
from internal.pkg.charts.utils import _parse_date_str

_BAR_COLOR = '#1976d2'


def create_bar_chart(shipments):
    configure_matplotlib()

    max_items = 200
    if len(shipments) > max_items:
        rng = random.Random(42)
        shipments = rng.sample(shipments, max_items)

    daily_counts = defaultdict(int)

    for shipment in shipments:
        delivery_date = _parse_date_str(shipment.get('actual_delivery'))
        if delivery_date is None:
            delivery_date = _parse_date_str(shipment.get('created_at'))
        if delivery_date is None:
            continue
        daily_counts[delivery_date] += 1

    if not daily_counts:
        return {'image_base64': None, 'data_info': {'error': '没有可用的数据生成柱状图'}}

    dates = sorted(daily_counts.keys())[-10:]
    counts = [daily_counts[d] for d in dates]

    if not dates:
        return {'image_base64': None, 'data_info': {'error': '数据不足，无法生成柱状图'}}

    fig, ax = plt.subplots(figsize=(max(8, len(dates) * 0.8), 5))

    x_pos = np.arange(len(dates))
    bars = ax.bar(x_pos, counts, color=_BAR_COLOR, alpha=0.85, edgecolor='white', linewidth=0.8, width=0.6)

    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height,
                f'{int(count)}',
                ha='center', va='bottom', fontsize=9, color='#333333')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.strftime('%m-%d') for d in dates], rotation=0, fontsize=9)
    ax.set_xlabel('日期')
    ax.set_ylabel('发货量')
    ax.set_title('每日发货量统计')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)

    return {
        'image_base64': image_base64,
        'data_info': {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'counts': counts
        }
    }
