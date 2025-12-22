# models/__init__.py
import json
import os

import pymysql
import ollama
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("LogisticsAgent")


def create_data_manager():
    """创建并返回基于 MySQL 的 LogisticsDataManager 实例"""
    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "rootroot")
    mysql_db = os.getenv("MYSQL_DATABASE", "logistics")

    return LogisticsDataManager(
        host=mysql_host,
        port=mysql_port,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db,
    )


def create_model_handler(model_name: str = "deepseek-r1:1.5b"):
    """创建并返回OllamaModelHandler实例"""
    return OllamaModelHandler(model_name)


class LogisticsDataManager:
    """物流数据管理器，使用 MySQL 存储数据"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._ensure_database()
        self._init_database()

    def _get_connection(self, with_db: bool = True):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database if with_db else None,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )

    def _ensure_database(self):
        """确保数据库存在"""
        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库（表结构）"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shipments (
                        id VARCHAR(128) PRIMARY KEY,
                        origin VARCHAR(255),
                        destination VARCHAR(255),
                        origin_city VARCHAR(255),
                        destination_city VARCHAR(255),
                        status VARCHAR(64),
                        estimated_delivery DATE,
                        actual_delivery DATE,
                        weight DOUBLE,
                        dimensions TEXT,
                        customer_id VARCHAR(128),
                        courier_company VARCHAR(255),
                        courier VARCHAR(255),
                        package_type VARCHAR(128),
                        priority VARCHAR(64),
                        customer_type VARCHAR(128),
                        payment_method VARCHAR(128),
                        shipping_fee DOUBLE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS shipment_events (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        shipment_id VARCHAR(128),
                        event_type VARCHAR(128),
                        location VARCHAR(255),
                        description TEXT,
                        timestamp DATETIME,
                        CONSTRAINT fk_shipment
                            FOREIGN KEY (shipment_id) REFERENCES shipments(id)
                            ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            conn.commit()
        finally:
            conn.close()

    def import_from_csv(self, file_path: str) -> Dict[str, Any]:
        """从CSV文件导入数据"""
        try:
            df = pd.read_csv(file_path)
            logger.info(f"CSV列名: {list(df.columns)}")
            logger.info(f"CSV行数: {len(df)}")
            
            shipments = df.to_dict('records')

            # 转换数据格式
            processed_shipments = []
            for i, shipment in enumerate(shipments):
                try:
                    # 安全的数据类型转换
                    def safe_float(value, default=0.0):
                        try:
                            if pd.isna(value) or value == '' or value is None:
                                return default
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_str(value, default=''):
                        try:
                            if pd.isna(value) or value is None:
                                return default
                            return str(value)
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_date(value):
                        try:
                            if pd.isna(value) or value == '' or value is None:
                                return None
                            return str(value)
                        except (ValueError, TypeError):
                            return None

                    processed_shipment = {
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
                    processed_shipments.append(processed_shipment)
                    
                except Exception as e:
                    logger.warning(f"处理第{i+1}条记录时出错: {e}")
                    continue

            if not processed_shipments:
                return {
                    "success": False,
                    "message": "没有成功处理任何数据记录"
                }

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
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }

    def clear_all_data(self) -> None:
        """清空所有数据（一次性 Agent 覆盖导入场景）"""
        conn = self._get_connection()
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
            import numpy as np

            df = pd.read_csv(BytesIO(file_bytes))
            logger.info(f"CSV列名: {list(df.columns)}")
            logger.info(f"CSV行数: {len(df)}")
            
            shipments = df.to_dict('records')

            processed_shipments = []
            for i, shipment in enumerate(shipments):
                try:
                    # 安全的数据类型转换
                    def safe_float(value, default=0.0):
                        try:
                            if pd.isna(value) or value == '' or value is None:
                                return default
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_str(value, default=''):
                        try:
                            if pd.isna(value) or value is None:
                                return default
                            return str(value)
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_date(value):
                        try:
                            if pd.isna(value) or value == '' or value is None:
                                return None
                            return str(value)
                        except (ValueError, TypeError):
                            return None

                    processed_shipment = {
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
                    processed_shipments.append(processed_shipment)
                    
                except Exception as e:
                    logger.warning(f"处理第{i+1}条记录时出错: {e}")
                    continue

            if not processed_shipments:
                return {
                    "success": False,
                    "message": "没有成功处理任何数据记录"
                }

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
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }

    def bulk_insert_shipments(self, shipments: List[Dict]):
        """批量插入物流数据"""
        conn = self._get_connection()
        cursor = conn.cursor()

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
            logger.info(f"成功插入 {len(shipments)} 条物流数据")

        except Exception as e:
            logger.error(f"插入数据时出错: {e}")
            conn.rollback()

        finally:
            conn.close()

    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict]:
        """根据ID获取物流信息"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM shipments WHERE id = %s', (shipment_id,))
                row = cursor.fetchone()
                if row:
                    row['dimensions'] = json.loads(row.get('dimensions') or '{}')
                    return row
                return None
        finally:
            conn.close()

    def get_all_shipments(self, limit: int = 10000) -> List[Dict]:
        """获取所有物流信息"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM shipments ORDER BY created_at DESC LIMIT %s', (int(limit),))
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    row['dimensions'] = json.loads(row.get('dimensions') or '{}')
                    result.append(row)
                return result
        finally:
            conn.close()

    def get_shipment_events(self, shipment_id: str) -> List[Dict]:
        """获取物流事件历史"""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM shipment_events WHERE shipment_id = %s ORDER BY timestamp', (shipment_id,))
                rows = cursor.fetchall()
                return rows
        finally:
            conn.close()

    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """获取每日统计信息"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) AS c FROM shipments WHERE DATE(created_at) = %s', (date,))
                total_shipments = cursor.fetchone()["c"]

                cursor.execute('SELECT COUNT(*) AS c FROM shipments WHERE DATE(actual_delivery) = %s', (date,))
                delivered = cursor.fetchone()["c"]

                cursor.execute(
                    'SELECT COUNT(*) AS c FROM shipments WHERE status = %s AND actual_delivery > estimated_delivery AND DATE(actual_delivery) = %s',
                    ("delivered", date,),
                )
                delayed = cursor.fetchone()["c"]
        finally:
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

    def __init__(self, model_name: str = "deepseek-r1:1.5b"):
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
        你是一个大型分拨中心的运营分析员。基于以下货件信息，按物流中心的现实业务给出可执行洞察：
        {self._format_shipment_data(shipment_data)}

        输出用简洁要点（每点≤20字），包含：
        1) 运营状态：是否异常、阻塞位置
        2) 风险预警：延误/错分/逆向等（概率+影响）
        3) 优先动作：今天需跟进的2-3个动作（含岗位）
        4) SLA 提醒：是否命中SLA阈值（建议缓解措施）
        """

        analysis = await self.generate_response(prompt)
        return {
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    async def analyze_bulk_data(self, shipments_data: List[Dict]) -> Dict:
        """批量分析物流数据"""
        prompt = f"""
        你是转运中心现场的班次值班经理。基于以下全量数据输出面向执行的班次简报：

        数据概览：
        - 总记录数: {len(shipments_data)}
        - 状态分布: {self._get_status_distribution(shipments_data)}
        - 平均重量: {self._calculate_average_weight(shipments_data):.2f} kg

        请严格按以下结构输出（短句要点式）：
        A. 今日运行态势（拥堵/异常波次/高峰时段）
        B. 风险清单（TOP3：场地、车辆、干线/支线）
        C. 产能与人力（分拣线利用率、缺口岗位与时段）
        D. 关键KPI（SLA命中率、滞留件、问题件、装车准点）
        E. 行动清单（≤5条，明确“责任岗位+完成时限”）
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
        生成运营日报（面向管理层的一页纸）：

        核心统计：发货{daily_stats.get('total_shipments', 0)}，交付{daily_stats.get('delivered', 0)}，
                 延迟{daily_stats.get('delayed', 0)}，准时率{daily_stats.get('on_time_rate', 0):.1f}%

        输出模块：
        1) 经营看板：SLA、吞吐、滞留走势（一句话趋势）
        2) 异常焦点：TOP2异常及影响（金额/客户/区域）
        3) 纠偏措施：已执行与待执行（负责人+截止时间）
        4) 明日安排：人车资源与产能计划（风险点）
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
