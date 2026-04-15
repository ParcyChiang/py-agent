import csv
import random
from datetime import datetime, timedelta


def generate_logistics_data(num_records=1000):
    """生成快递中心物流数据（季度内，更真实的快递场景）"""

    # 快递公司
    courier_companies = ['顺丰速运', '圆通速递', '中通快递', '申通快递', '韵达速递', '京东物流', '德邦快递']
    
    # 城市和区域（更真实的快递网络）
    cities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '南京', '重庆', '天津', '苏州']
    districts = ['朝阳区', '海淀区', '浦东新区', '天河区', '南山区', '西湖区', '锦江区', '江汉区', '雁塔区', '鼓楼区', '渝中区', '和平区', '姑苏区']
    
    # 快递状态（更符合实际流程）
    statuses = ['pending', 'processing', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed_delivery', 'returned']
    
    # 包裹类型
    package_types = ['文件', '电子产品', '服装', '食品', '日用品', '书籍', '化妆品', '药品', '生鲜', '其他']
    
    # 优先级
    priorities = ['standard', 'express', 'urgent', 'same_day']
    
    # 配送员
    couriers = [f'配送员{chr(65+i)}{str(j).zfill(2)}' for i in range(8) for j in range(1, 13)]  # A01-A12, B01-B12...
    
    # 客户类型
    customer_types = ['个人', '企业', '电商', 'VIP']
    
    # 支付方式
    payment_methods = ['货到付款', '在线支付', '月结', '预付费']
    
    customer_ids = [f'CUST{str(i).zfill(4)}' for i in range(1, 2001)]  # CUST0001 到 CUST2000

    # 生成数据
    data = []
    for i in range(num_records):
        shipment_id = f"SF{random.randint(100000, 999999)}"  # 更真实的快递单号格式
        
        # 生成起始地和目的地（城市+区域）
        origin_city = random.choice(cities)
        origin_district = random.choice(districts)
        origin = f"{origin_city}{origin_district}分拨中心"
        
        dest_city = random.choice(cities)
        dest_district = random.choice(districts)
        destination = f"{dest_city}{dest_district}"
        
        # 确保起始地和目的地不同
        while origin_city == dest_city:
            dest_city = random.choice(cities)
            dest_district = random.choice(districts)
            destination = f"{dest_city}{dest_district}"

        # 状态分布更真实（大部分已送达）
        status_weights = [0.05, 0.1, 0.15, 0.2, 0.3, 0.15, 0.03, 0.02]  # pending, processing, picked_up, in_transit, delivered, out_for_delivery, failed_delivery, returned
        status = random.choices(statuses, weights=status_weights)[0]
        
        # 包裹类型和重量相关
        package_type = random.choice(package_types)
        if package_type == '文件':
            weight = round(random.uniform(0.1, 2.0), 1)
        elif package_type == '电子产品':
            weight = round(random.uniform(0.5, 15.0), 1)
        elif package_type == '生鲜':
            weight = round(random.uniform(1.0, 10.0), 1)
        else:
            weight = round(random.uniform(0.2, 25.0), 1)
        
        # 尺寸根据重量调整
        base_size = max(5, int(weight * 2))
        length = random.randint(base_size, base_size + 20)
        width = random.randint(base_size//2, base_size//2 + 15)
        height = random.randint(base_size//3, base_size//3 + 10)

        # 时间控制在季度内（90天）
        days_ago = random.randint(0, 90)  # 最近90天内
        created_date = datetime.now() - timedelta(days=days_ago)
        
        # 根据优先级和距离计算预计送达时间
        priority = random.choices(priorities, weights=[0.6, 0.25, 0.1, 0.05])[0]  # 大部分标准件
        distance_days = 1 if origin_city == dest_city else random.randint(2, 5)
        
        if priority == 'same_day':
            est_delivery = created_date + timedelta(hours=random.randint(4, 12))
        elif priority == 'urgent':
            est_delivery = created_date + timedelta(days=1)
        elif priority == 'express':
            est_delivery = created_date + timedelta(days=distance_days)
        else:  # standard
            est_delivery = created_date + timedelta(days=distance_days + random.randint(0, 2))

        # 实际交付时间
        actual_delivery = None
        if status == 'delivered':
            # 实际交付时间可能在预计时间前后1天内
            delivery_offset = random.randint(-1, 1)
            actual_delivery = est_delivery + timedelta(days=delivery_offset)
        elif status in ['failed_delivery', 'returned']:
            # 失败或退回的包裹
            actual_delivery = est_delivery + timedelta(days=random.randint(1, 3))
        else:
            actual_delivery = ''

        # 其他字段
        customer_id = random.choice(customer_ids)
        courier_company = random.choice(courier_companies)
        courier = random.choice(couriers) if status in ['out_for_delivery', 'delivered', 'failed_delivery'] else ''
        customer_type = random.choices(customer_types, weights=[0.4, 0.3, 0.25, 0.05])[0]
        payment_method = random.choices(payment_methods, weights=[0.2, 0.5, 0.2, 0.1])[0]
        
        # 运费（根据重量、距离、优先级计算）
        base_fare = 8.0
        weight_fare = max(0, (weight - 1) * 2)  # 超重费
        distance_fare = 0 if origin_city == dest_city else random.uniform(2, 8)
        priority_fare = {'standard': 0, 'express': 5, 'urgent': 15, 'same_day': 25}[priority]
        shipping_fee = round(base_fare + weight_fare + distance_fare + priority_fare, 2)

        data.append({
            'id': shipment_id,
            'origin': origin,
            'destination': destination,
            'origin_city': origin_city,
            'destination_city': dest_city,
            'status': status,
            'estimated_delivery': est_delivery.strftime('%Y-%m-%d'),
            'actual_delivery': actual_delivery.strftime('%Y-%m-%d') if actual_delivery else '',
            'weight': weight,
            'length': length,
            'width': width,
            'height': height,
            'customer_id': customer_id,
            'courier_company': courier_company,
            'courier': courier,
            'package_type': package_type,
            'priority': priority,
            'customer_type': customer_type,
            'payment_method': payment_method,
            'shipping_fee': shipping_fee,
            'created_at': created_date.strftime('%Y-%m-%d %H:%M:%S')
        })

    return data


def save_to_csv(data, filename):
    """保存数据到CSV文件"""
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['id', 'origin', 'destination', 'origin_city', 'destination_city', 'status', 
                      'estimated_delivery', 'actual_delivery', 'weight', 'length', 'width', 'height', 
                      'customer_id', 'courier_company', 'courier', 'package_type', 'priority', 
                      'customer_type', 'payment_method', 'shipping_fee', 'created_at']

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