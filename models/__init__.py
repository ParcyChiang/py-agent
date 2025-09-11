# models/__init__.py
import json
import sqlite3

import ollama
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("LogisticsAgent")


def create_data_manager(db_path: str = "logistics.db"):
    """创建并返回LogisticsDataManager实例"""
    return LogisticsDataManager(db_path)


def create_model_handler(model_name: str = "qwen:0.5b"):
    """创建并返回OllamaModelHandler实例"""
    return OllamaModelHandler(model_name)


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

            # 覆盖导入：清空旧数据再写入
            self.clear_all_data()
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

    def clear_all_data(self) -> None:
        """清空所有数据（一次性 Agent 覆盖导入场景）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # 先清空事件表，再清空主表
            cursor.execute('DELETE FROM shipment_events')
            cursor.execute('DELETE FROM shipments')
            conn.commit()
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def import_from_csv_bytes(self, file_bytes: bytes) -> Dict[str, Any]:
        """从内存字节流导入CSV数据（无需落盘）"""
        try:
            from io import BytesIO

            df = pd.read_csv(BytesIO(file_bytes))
            shipments = df.to_dict('records')

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

            # 覆盖导入
            self.clear_all_data()
            self.bulk_insert_shipments(processed_shipments)

            return {
                "success": True,
                "message": f"成功导入 {len(processed_shipments)} 条物流数据",
                "count": len(processed_shipments)
            }
        except Exception as e:
            logger.error(f"从字节流导入CSV失败: {e}")
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

    def get_all_shipments(self, limit: int = 10000) -> List[Dict]:
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


class OllamaModelHandler:
    """Ollama模型处理器"""

    def __init__(self, model_name: str = "qwen-0.5b"):
        self.model_name = model_name

    async def generate_response(self, prompt: str, context: str = "") -> str:
        """使用Ollama生成响应"""
        try:
            # 构建完整的提示词
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': full_prompt}]
            )

            return response['message']['content']

        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    async def analyze_shipment_data(self, shipment_data: Dict) -> Dict:
        """分析物流数据"""
        prompt = f"""
        请分析以下物流数据并提供见解：
        {self._format_shipment_data(shipment_data)}

        请用简洁的语言提供：
        1. 当前状态评估
        2. 潜在风险（如有）
        3. 简要建议
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    async def analyze_bulk_data(self, shipments_data: List[Dict]) -> Dict:
        """批量分析物流数据"""
        prompt = f"""
        请分析以下物流数据集并提供整体见解：

        数据概览：
        - 总记录数: {len(shipments_data)}
        - 状态分布: {self._get_status_distribution(shipments_data)}
        - 平均重量: {self._calculate_average_weight(shipments_data):.2f} kg

       请用简洁的语言提供：
        1. 运营状况总结（50字内）
        2. 主要问题和建议（3条以内）
        3. 关键改进点
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_records": len(shipments_data),
                "status_distribution": self._get_status_distribution(shipments_data),
                "average_weight": self._calculate_average_weight(shipments_data)
            }
        }

    async def predict_delivery_time(self, shipment_data: Dict, historical_data: List[Dict] = None) -> Dict:
        """预测交付时间（简化版）"""
        context = "历史数据预测" if historical_data else "当前数据预测"

        prompt = f"""
        {context}

        当前货物：{shipment_data.get('id')}，{shipment_data.get('origin')}→{shipment_data.get('destination')}
        状态：{shipment_data.get('status')}，重量：{shipment_data.get('weight')}kg

        请预测交付时间（格式：X天，置信度：X%）
        """

        prediction = await self.generate_response(prompt)
        return {
            "prediction": prediction,
            "timestamp": datetime.now().isoformat()
        }

    async def generate_daily_report(self, daily_stats: Dict, shipments_data: List[Dict]) -> Dict:
        """生成每日报告（简化版）"""
        prompt = f"""
        生成物流日报：
        
         统计：发货{daily_stats.get('total_shipments', 0)}，交付{daily_stats.get('delivered', 0)}，
               延迟{daily_stats.get('delayed', 0)}，准时率{daily_stats.get('on_time_rate', 0):.1f}%

        请用简短文字描述：
        1. 告诉我发货量最多的是哪一天
        2. 主要问题（最多2点）
        3. 建议（1-2条）
        """

        report = await self.generate_response(prompt)

        return {
            "date": daily_stats.get('date'),
            "report": report,
            "statistics": daily_stats
        }

    def _get_status_distribution(self, shipments_data: List[Dict]) -> Dict[str, int]:
        """获取状态分布"""
        distribution = {}
        for shipment in shipments_data:
            status = shipment.get('status', 'unknown')
            distribution[status] = distribution.get(status, 0) + 1
        return distribution

    def _calculate_average_weight(self, shipments_data: List[Dict]) -> float:
        """计算平均重量"""
        if not shipments_data:
            return 0.0

        total_weight = sum(shipment.get('weight', 0) for shipment in shipments_data)
        return total_weight / len(shipments_data)

    def _format_sample_shipments(self, shipments_data: List[Dict]) -> str:
        """格式化样本数据用于提示词"""
        if not shipments_data:
            return "无数据"

        result = ""
        for i, shipment in enumerate(shipments_data, 1):
            result += f"{i}. ID: {shipment.get('id')}, 状态: {shipment.get('status')}, " \
                      f"从 {shipment.get('origin')} 到 {shipment.get('destination')}\n"

        return result
