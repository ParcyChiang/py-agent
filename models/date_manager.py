#数据管理类
import json
import sqlite3
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("LogisticsAgent")


class LogisticsDataManager:
    """物流数据管理器，处理大量物流数据"""

    def __init__(self, db_path: str = "logistics.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建物流数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipments (
            id TEXT PRIMARY KEY,
            origin TEXT,
            destination TEXT,
            status TEXT,
            estimated_delivery DATE,
            actual_delivery DATE,
            weight REAL,
            dimensions TEXT,
            customer_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 创建物流事件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id TEXT,
            event_type TEXT,
            location TEXT,
            description TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (shipment_id) REFERENCES shipments (id)
        )
        ''')

        conn.commit()
        conn.close()

    def import_from_csv(self, file_path: str) -> Dict[str, Any]:
        """从CSV文件导入数据"""
        try:
            df = pd.read_csv(file_path)
            shipments = df.to_dict('records')

            # 转换数据格式
            processed_shipments = []
            for shipment in shipments:
                processed_shipment = {
                    'id': str(shipment.get('id', '')),
                    'origin': str(shipment.get('origin', '')),
                    'destination': str(shipment.get('destination', '')),
                    'status': str(shipment.get('status', 'pending')),
                    'estimated_delivery': shipment.get('estimated_delivery'),
                    'actual_delivery': shipment.get('actual_delivery'),
                    'weight': float(shipment.get('weight', 0)),
                    'dimensions': {
                        'length': float(shipment.get('length', 0)),
                        'width': float(shipment.get('width', 0)),
                        'height': float(shipment.get('height', 0))
                    },
                    'customer_id': str(shipment.get('customer_id', ''))
                }
                processed_shipments.append(processed_shipment)

            self.bulk_insert_shipments(processed_shipments)

            return {
                "success": True,
                "message": f"成功导入 {len(processed_shipments)} 条物流数据",
                "count": len(processed_shipments)
            }

        except Exception as e:
            logger.error(f"导入CSV数据时出错: {e}")
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }

    def bulk_insert_shipments(self, shipments: List[Dict]):
        """批量插入物流数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for shipment in shipments:
                cursor.execute('''
                INSERT OR REPLACE INTO shipments 
                (id, origin, destination, status, estimated_delivery, actual_delivery, weight, dimensions, customer_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    shipment.get('id'),
                    shipment.get('origin'),
                    shipment.get('destination'),
                    shipment.get('status'),
                    shipment.get('estimated_delivery'),
                    shipment.get('actual_delivery'),
                    shipment.get('weight'),
                    json.dumps(shipment.get('dimensions', {})),
                    shipment.get('customer_id')
                ))

            conn.commit()
            logger.info(f"成功插入 {len(shipments)} 条物流数据")

        except Exception as e:
            logger.error(f"插入数据时出错: {e}")
            conn.rollback()

        finally:
            conn.close()

    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict]:
        """根据ID获取物流信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM shipments WHERE id = ?', (shipment_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['dimensions'] = json.loads(result['dimensions'])
            return result
        return None

    def get_all_shipments(self, limit: int = 100) -> List[Dict]:
        """获取所有物流信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM shipments ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            item = dict(row)
            item['dimensions'] = json.loads(item['dimensions'])
            result.append(item)

        return result

    def get_shipment_events(self, shipment_id: str) -> List[Dict]:
        """获取物流事件历史"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM shipment_events WHERE shipment_id = ? ORDER BY timestamp', (shipment_id,))
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """获取每日统计信息"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取当日发货总数
        cursor.execute('SELECT COUNT(*) FROM shipments WHERE DATE(created_at) = ?', (date,))
        total_shipments = cursor.fetchone()[0]

        # 获取当日已交付数量
        cursor.execute('SELECT COUNT(*) FROM shipments WHERE DATE(actual_delivery) = ?', (date,))
        delivered = cursor.fetchone()[0]

        # 获取延迟交付数量
        cursor.execute('''
        SELECT COUNT(*) FROM shipments 
        WHERE status = "delivered" AND actual_delivery > estimated_delivery
        AND DATE(actual_delivery) = ?
        ''', (date,))
        delayed = cursor.fetchone()[0]

        conn.close()

        return {
            "date": date,
            "total_shipments": total_shipments,
            "delivered": delivered,
            "delayed": delayed,
            "on_time_rate": (delivered - delayed) / delivered * 100 if delivered > 0 else 0
        }