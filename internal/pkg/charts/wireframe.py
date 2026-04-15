"""三维线框图 - 客户类型 x 优先级 x 状态"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
from mpl_toolkits.mplot3d import Axes3D
from collections import defaultdict

from internal.pkg.constants import STATUS_CN_MAP
from internal.pkg.utils import configure_matplotlib


def create_wireframe_plot(shipments):
    """生成三维线框图数据：客户类型 x 优先级 x 状态分布

    参数:
        shipments: 物流数据字典列表

    返回:
        包含 'image_base64' 和 'data_info' 的字典
    """
    configure_matplotlib()

    # 数据采样：超过100条时采样
    max_items = 100
    if len(shipments) > max_items:
        import random
        shipments = random.sample(shipments, max_items)
        print(f"线框图采样后数据: {len(shipments)} 条")

    # 准备线框图数据：客户类型 x 优先级 x 状态
    customer_priority_status_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for shipment in shipments:
        # 转换状态为中文
        status = shipment.get('status', '未知状态')
        status_cn = STATUS_CN_MAP.get(status, status)

        # 处理线框图数据
        customer_type = shipment.get('customer_type', '未知类型')
        priority = shipment.get('priority', '未知优先级')
        if customer_type != '未知类型' and priority != '未知优先级' and status_cn != '未知状态':
            customer_priority_status_data[customer_type][priority][status_cn] += 1

    # 调试信息
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

    # 线框图数据准备
    all_customer_types = sorted(list(customer_priority_status_data.keys()))
    all_priorities = sorted(list(set(priority for priority_data in customer_priority_status_data.values() for priority in priority_data.keys())))
    all_line_statuses = sorted(list(set(status for priority_data in customer_priority_status_data.values() for status_data in priority_data.values() for status in status_data.keys())))

    # 创建线框图数据矩阵
    X_wireframe = np.arange(len(all_customer_types))  # 客户类型索引
    Y_wireframe = np.arange(len(all_priorities))  # 优先级索引
    X_wireframe, Y_wireframe = np.meshgrid(X_wireframe, Y_wireframe)

    wireframe_data = {}
    for status in all_line_statuses:
        Z = np.zeros((len(all_priorities), len(all_customer_types)))
        for i, priority in enumerate(all_priorities):
            for j, customer_type in enumerate(all_customer_types):
                Z[i, j] = customer_priority_status_data.get(customer_type, {}).get(priority, {}).get(status, 0)
        wireframe_data[status] = Z

    # 生成三维线框图
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

    # 设置坐标轴标签
    ax.set_xticks(range(len(all_customer_types)))
    ax.set_xticklabels(all_customer_types, rotation=45)
    ax.set_yticks(range(len(all_priorities)))
    ax.set_yticklabels(all_priorities)

    ax.legend()

    # 转换为 base64 字符串
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
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
