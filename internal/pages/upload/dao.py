# pages/upload/dao.py
"""上传页面 DAO 层"""
import json
import contextlib
from typing import Dict, List, Any, Optional, Tuple

import pymysql
from pymysql.cursors import DictCursor

from internal.pkg.config import Config


class ShipmentDAO:
    """物流数据访问对象"""

    def __init__(self):
        self.host = Config.MYSQL_HOST
        self.port = Config.MYSQL_PORT
        self.user = Config.MYSQL_USER
        self.password = Config.MYSQL_PASSWORD
        self.database = Config.MYSQL_DATABASE

    def _get_connection(self, with_db: bool = True):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database if with_db else None,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )

    @contextlib.contextmanager
    def get_connection(self, with_db: bool = True):
        conn = self._get_connection(with_db)
        try:
            yield conn
        finally:
            conn.close()

    def import_from_csv_bytes(self, file_bytes: bytes) -> Dict[str, Any]:
        """从内存字节流导入CSV数据"""
        try:
            from io import BytesIO
            import pandas as pd

            df = pd.read_csv(BytesIO(file_bytes))
            shipments = df.to_dict('records')

            processed_shipments = []
            for i, shipment in enumerate(shipments):
                try:
                    processed_shipment = self._process_shipment_record(shipment)
                    processed_shipments.append(processed_shipment)
                except Exception as e:
                    print(f"处理第{i+1}条记录时出错: {e}")
                    continue

            if not processed_shipments:
                return {"success": False, "message": "没有成功处理任何数据记录"}

            self.clear_all_data()
            self.bulk_insert_shipments(processed_shipments)

            return {
                "success": True,
                "message": f"成功导入 {len(processed_shipments)} 条物流数据",
                "count": len(processed_shipments)
            }
        except Exception as e:
            print(f"从字节流导入CSV失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"导入失败: {str(e)}"}

    def _process_shipment_record(self, shipment: Dict) -> Dict:
        """处理单条物流记录"""
        from internal.pkg.utils import safe_float, safe_str, safe_date

        return {
            'id': safe_str(shipment.get('id', '')),
            'origin': safe_str(shipment.get('origin', '')),
            'destination': safe_str(shipment.get('destination', '')),
            'origin_city': safe_str(shipment.get('origin_city', '')),
            'destination_city': safe_str(shipment.get('destination_city', '')),
            'status': safe_str(shipment.get('status', 'pending')),
            'estimated_delivery': safe_date(shipment.get('estimated_delivery')),
            'actual_delivery': safe_date(shipment.get('actual_delivery')),
            'weight': safe_float(shipment.get('weight', 0)),
            'dimensions': {
                'length': safe_float(shipment.get('length', 0)),
                'width': safe_float(shipment.get('width', 0)),
                'height': safe_float(shipment.get('height', 0))
            },
            'customer_id': safe_str(shipment.get('customer_id', '')),
            'courier_company': safe_str(shipment.get('courier_company', '')),
            'courier': safe_str(shipment.get('courier', '')),
            'package_type': safe_str(shipment.get('package_type', '')),
            'priority': safe_str(shipment.get('priority', 'standard')),
            'customer_type': safe_str(shipment.get('customer_type', '')),
            'payment_method': safe_str(shipment.get('payment_method', '')),
            'shipping_fee': safe_float(shipment.get('shipping_fee', 0)),
            'created_at': safe_str(shipment.get('created_at', ''))
        }

    def clear_all_data(self) -> None:
        """清空所有数据"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute('DELETE FROM shipment_events')
                    cursor.execute('DELETE FROM shipments')
                    conn.commit()
                except Exception as e:
                    print(f"清空数据失败: {e}")
                    conn.rollback()
                    raise

    def bulk_insert_shipments(self, shipments: List[Dict]):
        """批量插入物流数据"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    for shipment in shipments:
                        cursor.execute(
                            """
                            INSERT INTO shipments
                            (id, origin, destination, origin_city, destination_city, status, estimated_delivery, actual_delivery,
                             weight, dimensions, customer_id, courier_company, courier, package_type, priority,
                             customer_type, payment_method, shipping_fee, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                origin=VALUES(origin),
                                destination=VALUES(destination),
                                origin_city=VALUES(origin_city),
                                destination_city=VALUES(destination_city),
                                status=VALUES(status),
                                estimated_delivery=VALUES(estimated_delivery),
                                actual_delivery=VALUES(actual_delivery),
                                weight=VALUES(weight),
                                dimensions=VALUES(dimensions),
                                customer_id=VALUES(customer_id),
                                courier_company=VALUES(courier_company),
                                courier=VALUES(courier),
                                package_type=VALUES(package_type),
                                priority=VALUES(priority),
                                customer_type=VALUES(customer_type),
                                payment_method=VALUES(payment_method),
                                shipping_fee=VALUES(shipping_fee),
                                created_at=VALUES(created_at)
                            """,
                            (
                                shipment.get('id'),
                                shipment.get('origin'),
                                shipment.get('destination'),
                                shipment.get('origin_city'),
                                shipment.get('destination_city'),
                                shipment.get('status'),
                                shipment.get('estimated_delivery'),
                                shipment.get('actual_delivery'),
                                shipment.get('weight'),
                                json.dumps(shipment.get('dimensions', {})),
                                shipment.get('customer_id'),
                                shipment.get('courier_company'),
                                shipment.get('courier'),
                                shipment.get('package_type'),
                                shipment.get('priority'),
                                shipment.get('customer_type'),
                                shipment.get('payment_method'),
                                shipment.get('shipping_fee'),
                                shipment.get('created_at'),
                            ),
                        )
                    conn.commit()
                    print(f"成功插入 {len(shipments)} 条物流数据")
                except Exception as e:
                    print(f"插入数据时出错: {e}")
                    conn.rollback()

    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict]:
        """根据ID获取物流信息"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM shipments WHERE id = %s', (shipment_id,))
                row = cursor.fetchone()
                if row:
                    row['dimensions'] = json.loads(row.get('dimensions') or '{}')
                    return row
                return None

    def get_all_shipments(self, limit: int = 10000, page: int = None, pageSize: int = None) -> Tuple[List[Dict], int]:
        """获取所有物流信息，支持分页"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) as total FROM shipments')
                total = cursor.fetchone()['total']

                if page is not None and pageSize is not None:
                    offset = (page - 1) * pageSize
                    cursor.execute(
                        'SELECT * FROM shipments ORDER BY created_at DESC LIMIT %s OFFSET %s',
                        (int(pageSize), int(offset))
                    )
                else:
                    cursor.execute(
                        'SELECT * FROM shipments ORDER BY created_at DESC LIMIT %s',
                        (int(limit),)
                    )
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    row['dimensions'] = json.loads(row.get('dimensions') or '{}')
                    result.append(row)
                return result, total

    def get_shipment_events(self, shipment_id: str) -> List[Dict]:
        """获取物流事件历史"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT * FROM shipment_events WHERE shipment_id = %s ORDER BY timestamp',
                    (shipment_id,)
                )
                return cursor.fetchall()

    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """获取每日统计信息"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                if date:
                    cursor.execute('SELECT COUNT(*) AS c FROM shipments WHERE DATE(created_at) = %s', (date,))
                    total_shipments = cursor.fetchone()["c"]
                    cursor.execute('SELECT COUNT(*) AS c FROM shipments WHERE DATE(actual_delivery) = %s', (date,))
                    delivered = cursor.fetchone()["c"]
                    cursor.execute(
                        'SELECT COUNT(*) AS c FROM shipments WHERE status = %s AND actual_delivery > estimated_delivery AND DATE(actual_delivery) = %s',
                        ("delivered", date,)
                    )
                    delayed = cursor.fetchone()["c"]
                else:
                    cursor.execute('SELECT COUNT(*) AS c FROM shipments')
                    total_shipments = cursor.fetchone()["c"]
                    cursor.execute('SELECT COUNT(*) AS c FROM shipments WHERE actual_delivery IS NOT NULL')
                    delivered = cursor.fetchone()["c"]
                    cursor.execute(
                        'SELECT COUNT(*) AS c FROM shipments WHERE status = %s AND actual_delivery > estimated_delivery',
                        ("delivered",)
                    )
                    delayed = cursor.fetchone()["c"]

                return {
                    "date": date if date else "all",
                    "total_shipments": total_shipments,
                    "delivered": delivered,
                    "delayed": delayed,
                    "on_time_rate": (delivered - delayed) / delivered * 100 if delivered > 0 else 0
                }

    def get_daily_trend(self) -> Dict[str, List[Dict]]:
        """获取每日趋势数据"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT DATE(created_at) AS date, COUNT(*) AS shipments
                    FROM shipments
                    GROUP BY DATE(created_at)
                    ORDER BY date
                ''')
                daily_shipments = cursor.fetchall()

                cursor.execute('''
                    SELECT DATE(actual_delivery) AS date, COUNT(*) AS delivered
                    FROM shipments
                    WHERE actual_delivery IS NOT NULL
                    GROUP BY DATE(actual_delivery)
                    ORDER BY date
                ''')
                daily_delivered = cursor.fetchall()

                cursor.execute('''
                    SELECT DATE(created_at) AS date, COUNT(*) AS in_transit
                    FROM shipments
                    WHERE status = 'in_transit'
                    GROUP BY DATE(created_at)
                    ORDER BY date
                ''')
                daily_in_transit = cursor.fetchall()

                return {
                    "shipments": daily_shipments,
                    "delivered": daily_delivered,
                    "in_transit": daily_in_transit
                }
