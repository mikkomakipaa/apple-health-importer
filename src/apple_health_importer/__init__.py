"""Apple Health Data Importer & Analytics Platform

Professional Apple Health data importer with comprehensive Grafana dashboards 
for health analytics and performance optimization.
"""

__version__ = "2.0.0"
__author__ = "Mikko Makipaa"
__email__ = "mikko@example.com"

# Main imports for easy access
from .main import main
from .config.manager import ConfigManager
from .config.enhanced import SecureConfigManager
from .parsers.health_data import HealthDataParser
from .writers.influxdb import InfluxDBWriter
from .validation.validator import HealthDataValidator

__all__ = [
    "main",
    "ConfigManager", 
    "SecureConfigManager",
    "HealthDataParser",
    "InfluxDBWriter", 
    "HealthDataValidator",
]