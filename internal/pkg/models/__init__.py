# internal/models/__init__.py
"""模型层"""
from internal.pkg.models.model_handler import AIModelHandler, create_model_handler

__all__ = ['AIModelHandler', 'create_model_handler']
