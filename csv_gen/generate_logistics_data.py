import csv
import random
from datetime import datetime, timedelta


def generate_logistics_data(num_records=1000):
    """生成物流数据（匹配deepseek_csv格式）"""

    # 定义可能的值（完全匹配您提供的格式）
    origins = ['上海仓库', '广州仓库', '北京仓库', '深圳仓库', '杭州仓库', '成都仓库']
    destinations = ['北京客户', '深圳客户', '上海客户', '广州客户', '杭州客户', '成都客户', '武汉客户']
    statuses = ['in_transit', 'delivered', 'pending', 'processing', 'out_for_delivery']
    customer_ids = [f'CUST{str(i).zfill(3)}' for i in range(1, 501)]  # CUST001 到 CUST500

    # 生成数据
    data = []
    for i in range(num_records):
        shipment_id = f"SH{1000 + i}"
        origin = random.choice(origins)
        destination = random.choice(destinations)

        # 确保起始地和目的地不同
        while origin.replace('仓库', '') == destination.replace('客户', ''):
            destination = random.choice(destinations)

        status = random.choice(statuses)
        weight = round(random.uniform(0.5, 50.0), 1)  # 保留1位小数
        length = random.randint(10, 100)
        width = random.randint(5, 50)
        height = random.randint(5, 40)

        # 生成时间（匹配您的格式）
        created_date = datetime.now() - timedelta(days=random.randint(0, 60))
        est_delivery = created_date + timedelta(days=random.randint(2, 15))

        actual_delivery = None
        if status == 'delivered':
            # 实际交付时间可能在预计时间前后2天内
            delivery_offset = random.randint(-2, 2)
            actual_delivery = est_delivery + timedelta(days=delivery_offset)
        elif status == 'in_transit':
            # 运输中的货物没有实际交付时间
            actual_delivery = ''
        else:
            # 其他状态也没有实际交付时间
            actual_delivery = ''

        customer_id = random.choice(customer_ids)

        data.append({
            'id': shipment_id,
            'origin': origin,
            'destination': destination,
            'status': status,
            'estimated_delivery': est_delivery.strftime('%Y-%m-%d'),
            'actual_delivery': actual_delivery.strftime('%Y-%m-%d') if actual_delivery else '',
            'weight': weight,
            'length': length,
            'width': width,
            'height': height,
            'customer_id': customer_id
        })

    return data


def save_to_csv(data, filename):
    """保存数据到CSV文件"""
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['id', 'origin', 'destination', 'status', 'estimated_delivery',
                      'actual_delivery', 'weight', 'length', 'width', 'height', 'customer_id']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"已生成 {len(data)} 条数据到 {filename}")


def generate_sample_files():
    """生成不同规模的样本文件"""
    print("开始生成物流数据...")

    # 生成100条数据（测试用）
    small_data = generate_logistics_data(100)
    save_to_csv(small_data, 'logistics_sample_100.csv')
    print("✓ 100条样本数据生成完成")

    # 生成1000条数据（中等规模）
    medium_data = generate_logistics_data(1000)
    save_to_csv(medium_data, 'logistics_sample_1000.csv')
    print("✓ 1000条样本数据生成完成")

    # 生成5000条数据（大规模）
    large_data = generate_logistics_data(5000)
    save_to_csv(large_data, 'logistics_sample_5000.csv')
    print("✓ 5000条样本数据生成完成")

    # 生成10000条数据（超大规模）
    xl_data = generate_logistics_data(10000)
    save_to_csv(xl_data, 'logistics_sample_10000.csv')
    print("✓ 10000条样本数据生成完成")

    print("\n所有文件生成完成！")
    print("生成的文件：")
    print("- logistics_sample_100.csv (100条，用于测试)")
    print("- logistics_sample_1000.csv (1000条，中等规模)")
    print("- logistics_sample_5000.csv (5000条，大规模)")
    print("- logistics_sample_10000.csv (10000条，超大规模)")

    # 显示前几条数据的预览
    print("\n数据预览（前3条）：")
    for i, row in enumerate(small_data[:3]):
        print(f"{i + 1}. {row}")


def generate_custom_file():
    """生成自定义数量的文件"""
    try:
        num_records = int(input("请输入要生成的记录数量: "))
        filename = input("请输入文件名（不含.csv）: ") + ".csv"

        data = generate_logistics_data(num_records)
        save_to_csv(data, filename)

        print(f"\n✓ 成功生成 {num_records} 条数据到 {filename}")
        print("前3条数据预览：")
        for i, row in enumerate(data[:3]):
            print(f"{i + 1}. {row}")

    except ValueError:
        print("请输入有效的数字！")


if __name__ == "__main__":
    print("物流数据生成器")
    print("=" * 50)
    print("1. 生成标准样本文件（100/1000/5000/10000条）")
    print("2. 生成自定义数量的文件")

    choice = input("请选择 (1 或 2): ")

    if choice == "1":
        generate_sample_files()
    elif choice == "2":
        generate_custom_file()
    else:
        print("无效选择，生成标准样本文件...")
        generate_sample_files()