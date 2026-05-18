"""折线图 - 时间趋势分析"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
import random
from collections import defaultdict

from internal.pkg.constants import STATUS_CN_MAP
from internal.pkg.utils import configure_matplotlib
from internal.pkg.charts.utils import _parse_date_str

_LINE_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#795548']


def create_line_chart(shipments):
    configure_matplotlib()

    max_items = 200
    if len(shipments) > max_items:
        rng = random.Random(42)
        shipments = rng.sample(shipments, max_items)

    daily_status_data = defaultdict(lambda: defaultdict(int))

    for shipment in shipments:
        status = shipment.get('status', '')
        status_cn = STATUS_CN_MAP.get(status, status)
        if not status_cn or status_cn == '未知状态':
            continue

        delivery_date = _parse_date_str(shipment.get('actual_delivery'))
        if delivery_date is None:
            delivery_date = _parse_date_str(shipment.get('created_at'))
        if delivery_date is None:
            continue

        daily_status_data[delivery_date][status_cn] += 1

    if not daily_status_data:
        return {'image_base64': None, 'data_info': {'error': '没有可用的数据生成折线图'}}

    dates = sorted(daily_status_data.keys())[-10:]

    if len(dates) < 2:
        return {'image_base64': None, 'data_info': {'error': '数据不足，无法生成折线图'}}

    status_totals = defaultdict(int)
    for day_data in daily_status_data.values():
        for status, count in day_data.items():
            status_totals[status] += count

    statuses = [s for s, _ in sorted(status_totals.items(), key=lambda x: -x[1])][:5]

    line_data = {}
    for status in statuses:
        line_data[status] = [daily_status_data[d].get(status, 0) for d in dates]

    fig, ax = plt.subplots(figsize=(max(8, len(dates) * 1.2), 5))

    x_pos = np.arange(len(dates))

    for i, (status, values) in enumerate(line_data.items()):
        color = _LINE_COLORS[i % len(_LINE_COLORS)]
        ax.plot(x_pos, values, marker='o', markersize=6, linewidth=2.5,
                color=color, label=status, alpha=0.9)
        for x, y in zip(x_pos, values):
            if y > 0:
                ax.text(x, y + 0.3, str(int(y)), ha='center', va='bottom', fontsize=7, color=color)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([d.strftime('%m-%d') for d in dates], rotation=0, fontsize=9)
    ax.set_xlabel('日期')
    ax.set_ylabel('发货量')
    ax.set_title('发货趋势分析')

    ax.legend(loc='upper right', fontsize=9)

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
            'statuses': statuses,
            'line_data': {k: v for k, v in line_data.items()}
        }
    }
