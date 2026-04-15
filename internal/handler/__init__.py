# internal/handler/__init__.py
"""HTTP 处理层"""
from internal.handler.shipment import ShipmentHandler
from internal.handler.auth import AuthHandler
from internal.handler.analysis import AnalysisHandler
from internal.handler.dashboard import DashboardHandler
from internal.handler.code_gen import CodeGenHandler

__all__ = [
    'ShipmentHandler',
    'AuthHandler',
    'AnalysisHandler',
    'DashboardHandler',
    'CodeGenHandler'
]
