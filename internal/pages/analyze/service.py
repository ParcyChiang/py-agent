# pages/analyze/service.py
"""分析页面服务层"""
import asyncio
from typing import Dict, Any

from internal.pages.upload.dao import ShipmentDAO
from internal.models.model_handler import MiniMaxModelHandler
from internal.pkg.utils import format_ai_response


class AnalyzeService:
    """AI分析服务"""
    def __init__(self):
        self.shipment_dao = ShipmentDAO()
        self.model_handler = MiniMaxModelHandler()