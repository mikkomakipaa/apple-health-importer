#!/usr/bin/env python3

import os
import yaml
import logging
from typing import Dict, Optional
from pathlib import Path


class SecureConfigManager:
    """Enhanced configuration manager with environment variable support and security features."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv('CONFIG_PATH', 'config.yaml')
        self.config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration with environment variable override support."""
        # Start with defaults
        self.config = self._get_default_config()
        
        # Load from file if it exists
        if Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                self._merge_configs(self.config, file_config)
                logging.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logging.warning(f"Error loading config file {self.config_path}: {e}")
        
        # Override with environment variables (highest priority)
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration values."""
        return {
            'influxdb': {
                'url': 'http://localhost:8086',
                'username': '',
                'password': '',
                'token': '',
                'org': 'default',
                'bucket': 'apple_health',
                'database': 'apple_health'
            },
            'homeassistant': {
                'url': '',
                'token': '',
                'enabled': False
            },
            'processing': {
                'timezone': 'UTC',
                'min_time_between': 60,
                'batch_size': 1000
            },
            'security': {
                'max_file_size_mb': 1024,
                'allowed_extensions': ['.xml'],
                'enable_audit_log': True,
                'validate_ssl': True
            },
            'logging': {
                'level': 'INFO',
                'file': None,
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            }
        }
    
    def _merge_configs(self, base: Dict, override: Dict) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            # InfluxDB settings
            'INFLUXDB_URL': ('influxdb', 'url'),
            'INFLUXDB_USERNAME': ('influxdb', 'username'),
            'INFLUXDB_PASSWORD': ('influxdb', 'password'),
            'INFLUXDB_TOKEN': ('influxdb', 'token'),
            'INFLUXDB_ORG': ('influxdb', 'org'),
            'INFLUXDB_BUCKET': ('influxdb', 'bucket'),
            'INFLUXDB_DATABASE': ('influxdb', 'database'),
            
            # Home Assistant settings
            'HOMEASSISTANT_URL': ('homeassistant', 'url'),
            'HOMEASSISTANT_TOKEN': ('homeassistant', 'token'),
            
            # Processing settings
            'TIMEZONE': ('processing', 'timezone'),
            'BATCH_SIZE': ('processing', 'batch_size'),
            
            # Security settings
            'MAX_FILE_SIZE_MB': ('security', 'max_file_size_mb'),
            'VALIDATE_SSL': ('security', 'validate_ssl'),
            
            # Logging settings
            'LOG_LEVEL': ('logging', 'level'),
            'LOG_FILE': ('logging', 'file')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if key in ['batch_size', 'max_file_size_mb', 'min_time_between']:
                    try:
                        value = int(value)
                    except ValueError:
                        logging.warning(f"Invalid integer value for {env_var}: {value}")
                        continue
                elif key in ['validate_ssl', 'enable_audit_log']:
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                self.config[section][key] = value
                logging.debug(f"Applied environment override: {env_var}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        errors = []
        
        # Validate InfluxDB configuration
        if not self.config['influxdb']['url']:
            errors.append("InfluxDB URL is required")
        
        # Validate authentication - either token OR username/password
        influx_config = self.config['influxdb']
        has_token = bool(influx_config.get('token'))
        has_credentials = bool(influx_config.get('username')) and bool(influx_config.get('password'))
        
        if not (has_token or has_credentials):
            errors.append("InfluxDB authentication required: either token or username/password")
        
        # Validate processing settings
        if self.config['processing']['batch_size'] <= 0:
            errors.append("Batch size must be positive")
        
        # Validate security settings
        if self.config['security']['max_file_size_mb'] <= 0:
            errors.append("Max file size must be positive")
        
        if errors:
            raise ValueError("Configuration validation failed: " + "; ".join(errors))
    
    def get(self, section: str, key: str, default=None):
        """Get configuration value with default fallback."""
        return self.config.get(section, {}).get(key, default)
    
    def get_section(self, section: str) -> Dict:
        """Get entire configuration section."""
        return self.config.get(section, {}).copy()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        if feature == 'homeassistant':
            ha_config = self.get_section('homeassistant')
            return ha_config.get('enabled', False) and bool(ha_config.get('token'))
        elif feature == 'audit_log':
            return self.get('security', 'enable_audit_log', False)
        elif feature == 'ssl_validation':
            return self.get('security', 'validate_ssl', True)
        
        return False
    
    def get_credentials_masked(self) -> Dict:
        """Get configuration with sensitive values masked for logging."""
        masked_config = {}
        for section, values in self.config.items():
            masked_config[section] = {}
            for key, value in values.items():
                if key in ['password', 'token', 'username'] and value:
                    masked_config[section][key] = '*' * 8
                else:
                    masked_config[section][key] = value
        
        return masked_config
    
    def validate_file_upload(self, filepath: str) -> bool:
        """Validate uploaded file meets security requirements."""
        path = Path(filepath)
        
        # Check file exists
        if not path.exists():
            logging.error(f"File does not exist: {filepath}")
            return False
        
        # Check file extension
        allowed_extensions = self.get('security', 'allowed_extensions', ['.xml'])
        if path.suffix.lower() not in allowed_extensions:
            logging.error(f"File extension not allowed: {path.suffix}")
            return False
        
        # Check file size
        max_size_mb = self.get('security', 'max_file_size_mb', 1024)
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            logging.error(f"File too large: {size_mb:.1f}MB > {max_size_mb}MB")
            return False
        
        return True
    
    def setup_logging(self) -> None:
        """Setup logging based on configuration."""
        level = getattr(logging, self.get('logging', 'level', 'INFO').upper())
        format_str = self.get('logging', 'format', '%(asctime)s - %(levelname)s - %(message)s')
        log_file = self.get('logging', 'file')
        
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(console_handler)
        
        # File handler if specified
        if log_file:
            try:
                # Create log directory if needed
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level)
                file_handler.setFormatter(logging.Formatter(format_str))
                handlers.append(file_handler)
            except Exception as e:
                logging.warning(f"Could not setup file logging: {e}")
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            format=format_str,
            handlers=handlers,
            force=True
        )
    
    def save_template(self, template_path: str) -> None:
        """Save a configuration template with environment variable placeholders."""
        template = {
            'influxdb': {
                'url': '${INFLUXDB_URL:-http://localhost:8086}',
                'token': '${INFLUXDB_TOKEN}',
                'org': '${INFLUXDB_ORG:-default}',
                'bucket': '${INFLUXDB_BUCKET:-apple_health}'
            },
            'homeassistant': {
                'url': '${HOMEASSISTANT_URL}',
                'token': '${HOMEASSISTANT_TOKEN}',
                'enabled': '${HOMEASSISTANT_ENABLED:-false}'
            },
            'processing': {
                'timezone': '${TIMEZONE:-UTC}',
                'min_time_between': '${MIN_TIME_BETWEEN:-60}',
                'batch_size': '${BATCH_SIZE:-1000}'
            },
            'security': {
                'max_file_size_mb': '${MAX_FILE_SIZE_MB:-1024}',
                'allowed_extensions': ['.xml'],
                'enable_audit_log': '${ENABLE_AUDIT_LOG:-true}',
                'validate_ssl': '${VALIDATE_SSL:-true}'
            },
            'logging': {
                'level': '${LOG_LEVEL:-INFO}',
                'file': '${LOG_FILE}',
                'format': '%(asctime)s - %(levelname)s - %(message)s'
            }
        }
        
        with open(template_path, 'w') as f:
            yaml.dump(template, f, default_flow_style=False, indent=2)
        
        logging.info(f"Configuration template saved to {template_path}")


if __name__ == '__main__':
    # Test the secure config manager
    config = SecureConfigManager()
    config.setup_logging()
    
    print("Configuration sections:")
    for section in config.config.keys():
        print(f"  - {section}")
    
    print("\nMasked configuration:")
    import json
    print(json.dumps(config.get_credentials_masked(), indent=2))