"""三维曲面图 - 城市 x 时间 x 状态"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Patch
import base64
import io
import random
from collections import defaultdict

from internal.pkg.constants import STATUS_CN_MAP
from internal.pkg.utils import configure_matplotlib
from internal.pkg.charts.utils import _parse_date_str

# 状态对应的 colormap，视觉区分度高
_STATUS_CMAPS = [
    cm.Reds, cm.Blues, cm.Greens, cm.Oranges, cm.Purples, cm.YlOrBr,
]
_STATUS_COLORS = ['#d32f2f', '#1976d2', '#388e3c', '#f57c00', '#7b1fa2', '#795548']


def create_surface_plot(shipments):
    """生成三维曲面图：城市 x 时间 x 状态分布

    对数据中实际存在的状态分别绘制曲面，使用 colormap 渐变着色，
    通过高斯平滑使曲面更连续美观。

    参数:
        shipments: 物流数据字典列表

    返回:
        包含 'image_base64' 和 'data_info' 的字典
    """
    configure_matplotlib()

    # 数据采样：超过200条时采样（固定种子保证可复现）
    max_items = 200
    if len(shipments) > max_items:
        rng = random.Random(42)
        shipments = rng.sample(shipments, max_items)

    # 聚合数据：日期 -> 城市 -> 状态 -> 数量
    time_city_status = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

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

        city = shipment.get('origin_city', '')
        if not city or city == '未知城市':
            continue

        time_city_status[delivery_date][city][status_cn] += 1

    if not time_city_status:
        return {
            'image_base64': None,
            'data_info': {
                'cities': [],
                'time_labels': [],
                'statuses': [],
                'error': '没有可用的数据生成三维图表'
            }
        }

    # 取最近7天数据
    all_dates = sorted(time_city_status.keys())
    dates = all_dates[-7:]

    # 只保留数据中实际出现的状态和城市（按数量排序取 top）
    city_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for day_data in time_city_status.values():
        for city, statuses in day_data.items():
            for status, count in statuses.items():
                city_counts[city] += count
                status_counts[status] += count

    cities = [c for c, _ in sorted(city_counts.items(), key=lambda x: -x[1])][:8]
    statuses = [s for s, _ in sorted(status_counts.items(), key=lambda x: -x[1])][:6]

    if not cities or not statuses:
        return {
            'image_base64': None,
            'data_info': {
                'cities': [],
                'time_labels': [],
                'statuses': [],
                'error': '数据维度不足，无法生成曲面图'
            }
        }

    # 构建网格
    X = np.arange(len(cities))
    Y = np.arange(len(dates))
    X_mesh, Y_mesh = np.meshgrid(X, Y)

    # 为每个状态构建 Z 矩阵
    surface_data = {}
    for status in statuses:
        Z = np.zeros((len(dates), len(cities)))
        for i, day in enumerate(dates):
            for j, city in enumerate(cities):
                Z[i, j] = time_city_status[day][city][status]
        # 高斯平滑使曲面更连续（仅在数据点足够时）
        if Z.shape[0] >= 3 and Z.shape[1] >= 3:
            Z = _gaussian_smooth(Z, sigma=0.6)
        surface_data[status] = Z

    # 绘图
    fig = plt.figure(figsize=(14, 9))
    ax = fig.add_subplot(111, projection='3d')

    legend_patches = []
    for i, (status, Z) in enumerate(surface_data.items()):
        cmap = _STATUS_CMAPS[i % len(_STATUS_CMAPS)]
        # 归一化 Z 值用于 colormap 映射
        z_max = Z.max()
        facecolors = cmap(Z / z_max * 0.8 + 0.2) if z_max > 0 else cmap(np.zeros_like(Z))
        ax.plot_surface(
            X_mesh, Y_mesh, Z,
            facecolors=facecolors,
            alpha=0.75,
            linewidth=0.3,
            edgecolor='gray',
            antialiased=True,
            shade=True,
        )
        legend_patches.append(Patch(color=_STATUS_COLORS[i % len(_STATUS_COLORS)], label=status))

    # 坐标轴
    ax.set_xticks(range(len(cities)))
    ax.set_xticklabels(cities, rotation=30, ha='right', fontsize=9)
    ax.set_yticks(range(len(dates)))
    ax.set_yticklabels([d.strftime('%m-%d') for d in dates], fontsize=9)
    ax.set_xlabel('城市', fontsize=11, labelpad=10)
    ax.set_ylabel('时间', fontsize=11, labelpad=10)
    ax.set_zlabel('数量', fontsize=11, labelpad=8)
    ax.set_title('三维曲面图 — 城市 × 时间 × 状态分布', fontsize=13, pad=20)

    # 图例（放在图外右上角）
    ax.legend(handles=legend_patches, loc='upper left', bbox_to_anchor=(1.02, 1),
              fontsize=9, framealpha=0.9)

    # 视角调整
    ax.view_init(elev=25, azim=-50)

    # 输出
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)

    return {
        'image_base64': image_base64,
        'data_info': {
            'cities': cities,
            'time_labels': [d.strftime('%m-%d') for d in dates],
            'statuses': list(statuses),
            'surface_data': {k: v.tolist() for k, v in surface_data.items()}
        }
    }


def _gaussian_smooth(Z, sigma=1.0):
    """简单高斯平滑，避免引入 scipy 依赖"""
    kernel_size = 3
    x = np.arange(kernel_size) - kernel_size // 2
    kernel_1d = np.exp(-x ** 2 / (2 * sigma ** 2))
    kernel_1d /= kernel_1d.sum()

    # 先按行卷积，再按列卷积
    smoothed = np.apply_along_axis(lambda row: np.convolve(row, kernel_1d, mode='same'), axis=1, arr=Z)
    smoothed = np.apply_along_axis(lambda col: np.convolve(col, kernel_1d, mode='same'), axis=0, arr=smoothed)
    # 保证非负
    return np.maximum(smoothed, 0)
