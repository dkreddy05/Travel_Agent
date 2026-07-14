"""wanderai/config — Configuration registry."""

from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

__all__ = [
    "BaseConfig",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
    "config_map",
]
