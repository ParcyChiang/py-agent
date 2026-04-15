"""三维散点图 - 重量 x 运费 x 城市"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
from mpl_toolkits.mplot3d import Axes3D

from internal.pkg.utils import configure_matplotlib


def create_scatter_plot(shipments):
    """生成三维散点图数据：重量 x 运费 x 城市分布

    参数:
        shipments: 物流数据字典列表

    返回:
        包含 'image_base64' 和 'data_info' 的字典
    """
    configure_matplotlib()

    # 准备散点图数据：重量 x 运费 x 城市
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

    # 调试信息
    print(f"散点图原始数据点数量: {len(weight_fee_city_data)}")

    # 数据采样：超过100点时采样
    max_points = 100
    if len(weight_fee_city_data) > max_points:
        import random
        weight_fee_city_data = random.sample(weight_fee_city_data, max_points)
        print(f"散点图采样后数据点数量: {len(weight_fee_city_data)}")

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

    # 散点图数据准备
    unique_cities = sorted(list(set(item['city'] for item in weight_fee_city_data)))
    city_to_index = {city: i for i, city in enumerate(unique_cities)}

    # 生成三维散点图
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # 为不同城市分配颜色
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']
    city_colors = {city: colors[i % len(colors)] for i, city in enumerate(unique_cities)}

    # 批量绘制散点图 - 按城市分组一次性绘制
    for city in unique_cities:
        city_items = [item for item in weight_fee_city_data if item['city'] == city]
        weights = [item['weight'] for item in city_items]
        fees = [item['shipping_fee'] for item in city_items]
        city_idx = city_to_index[city]

        ax.scatter(weights, fees, [city_idx] * len(city_items),
                  c=city_colors[city], label=city, s=50, alpha=0.7)

    # 只显示唯一的城市标签
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    ax.set_xlabel('重量 (kg)')
    ax.set_ylabel('运费 (元)')
    ax.set_zlabel('城市')
    ax.set_title('三维散点图 - 重量x运费x城市分布')

    # 设置 z 轴标签
    ax.set_zticks(range(len(unique_cities)))
    ax.set_zticklabels(unique_cities)

    # 移除 tight_layout 避免警告

    # 转换为 base64 字符串
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
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
