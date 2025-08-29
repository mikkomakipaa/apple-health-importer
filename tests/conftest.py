"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

# Add src directory to path so we can import our modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import Mock
import tempfile
import os


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_content = """
influxdb:
  url: http://localhost:8086
  username: test_user
  password: test_password
  database: test_db

processing:
  timezone: UTC
  batch_size: 100
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        f.flush()
        yield f.name
    
    # Cleanup
    os.unlink(f.name)


@pytest.fixture
def mock_influxdb_client():
    """Mock InfluxDB client for testing."""
    mock_client = Mock()
    mock_client.query.return_value = []
    mock_client.write_points.return_value = True
    return mock_client


@pytest.fixture
def sample_health_record():
    """Sample Apple Health XML record for testing."""
    return {
        'type': 'HKQuantityTypeIdentifierHeartRate',
        'value': '75',
        'startDate': '2024-01-01 12:00:00 +0000',
        'sourceName': 'Apple Watch'
    }