# 🏥 Apple Health Data Importer & Analytics Platform

Professional Apple Health data importer with comprehensive Grafana dashboards for health analytics and performance optimization. Transform your iPhone health data into enterprise-grade insights with advanced metrics like readiness scoring, training load analysis, and stress monitoring.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security](https://img.shields.io/badge/Security-Enhanced-green.svg)](docs/security_improvements.md)
[![Performance](https://img.shields.io/badge/Performance-14k%2B%20records%2Fsec-brightgreen.svg)](docs/final_swarm_report.md)

## 🚀 Features

### Core Capabilities
- **📊 Multi-Platform Integration**: InfluxDB storage + Home Assistant sensors + Grafana visualization
- **🏥 Comprehensive Health Data**: Heart rate, workouts, activity summaries, sleep analysis, calories
- **⚡ High Performance**: Streaming processing for files up to multi-GB size (14k+ elements/sec)
- **🔄 Smart Import Management**: Incremental imports, duplicate detection, resume capability
- **🛡️ Enhanced Data Quality**: Improved validation pipeline with robust error handling
- **🔧 Highly Configurable**: External YAML configuration for all settings
- **🩺 Advanced Analytics**: Readiness scoring, training load analysis, stress monitoring

### Performance & Reliability
- **Memory Efficient**: Processes 1GB+ files using only 200-500MB RAM
- **Fault Tolerant**: Resume interrupted imports from checkpoints  
- **Batch Processing**: Configurable batch sizes with retry logic
- **Progress Tracking**: Real-time progress bars with ETA
- **Duplicate Prevention**: Intelligent timestamp-based duplicate detection
- **Robust Parsing**: Enhanced datetime parsing with multiple format support
- **Smart Validation**: Relaxed heart rate limits for sleep data accuracy

### Enterprise Features ✨ **NEW**
- **Enhanced Security**: Environment variable support, credential masking, automated security scanning
- **Performance Optimization**: 14k+ records/second processing with smart batching and parallel processing
- **Advanced Configuration**: `enhanced_config.py` with validation and auto-optimization
- **Production Deployment**: Automated deployment scripts with Docker/Kubernetes support
- **Comprehensive Monitoring**: Performance metrics, bottleneck analysis, and health checks
- **Import History**: Track all imports with detailed statistics
- **Security Guidelines**: Comprehensive credential management documentation
- **Flexible Configuration**: External measurement mappings and validation rules
- **Extensive Logging**: Detailed logs for monitoring and debugging
- **Unit Tests**: Comprehensive test coverage for reliability

## 📋 Prerequisites

- **Python 3.8 or higher**
- **InfluxDB instance** (local or remote)
- **Home Assistant instance** (optional)
- **Apple Health data export** (XML format from iPhone)

## 🛠️ Installation

### Option 1: Automated Secure Setup ✨ **RECOMMENDED**
```bash
git clone https://github.com/mikkomakipaa/apple-health-importer.git
cd apple-health-importer

# Set your credentials as environment variables
export INFLUXDB_URL="https://your-influxdb:8086"
export INFLUXDB_TOKEN="your-secure-token"
export HOMEASSISTANT_URL="https://your-ha:8123"
export HOMEASSISTANT_TOKEN="your-ha-token"

# Run automated deployment
chmod +x scripts/secure_deploy.sh
./scripts/secure_deploy.sh
```

### Option 2: Manual Installation
```bash
git clone https://github.com/mikkomakipaa/apple-health-importer.git
cd apple-health-importer

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp config.yaml.example config.yaml
nano config.yaml  # Edit with your settings
```

**Required configuration:**
```yaml
# InfluxDB connection
influxdb:
  url: "http://your-influxdb-host:8086"
  username: "your-username" 
  password: "your-password"
  database: "apple_health"

# Processing settings
processing:
  timezone: "Your/Timezone"  # e.g., "America/New_York"
```

## 📱 Exporting Apple Health Data

1. Open **Health app** on iPhone
2. Tap your **profile picture** (top right)
3. Select **"Export All Health Data"**
4. Choose **"Export"** and save the ZIP file
5. Extract the ZIP to get `export.xml`

## 🚀 Usage

### Basic Import
```bash
# Import Apple Health data
python import_health_data.py export.xml
```

### Large File Optimization (1GB+)
```bash
# Automatic streaming mode for files >100MB
python import_health_data.py large_export.xml

# Force streaming mode
python import_health_data.py export.xml --streaming

# Preview what will be imported (safe for large files)
python import_health_data.py export.xml --preview
```

### Smart Import Management
```bash
# Incremental import - only new data since last import
python import_health_data.py new_export.xml --incremental

# Resume interrupted import
python import_health_data.py export.xml --resume

# Force re-import even if already processed
python import_health_data.py export.xml --force
```

### Import History & Management
```bash
# View import history and statistics
python import_health_data.py --show-history

# Reset import tracking (fresh start)
python import_health_data.py --reset-history
```

### Advanced Usage
```bash
# Custom configuration file
python import_health_data.py export.xml --config custom_config.yaml

# Combine multiple options
python import_health_data.py export.xml --incremental --streaming --preview
```

## 📊 Supported Data Types

| Data Type | InfluxDB Measurement | Home Assistant Entity | Description |
|-----------|---------------------|----------------------|-------------|
| **Heart Rate** | `heartrate_bpm` | `sensor.health_heart_rate` | BPM with motion context |
| **Workouts** | `energy_kcal` | `sensor.health_last_workout` | Duration, calories, distance |
| **Active Calories** | `energy_kcal` | `sensor.health_active_calories` | Daily active energy |
| **Resting Calories** | `energy_kcal` | `sensor.health_resting_calories` | Daily resting energy |
| **Sleep Analysis** | `sleep_duration_min` | `sensor.health_sleep_state` | Sleep duration and quality |
| **Activity Summary** | `energy_kcal` | `sensor.health_activity` | Daily move/exercise/stand |

## ⚙️ Configuration

### Core Configuration (`config.yaml`)
```yaml
# InfluxDB Configuration
influxdb:
  url: "http://localhost:8086"
  username: "admin"
  password: "password"
  database: "apple_health"

# Home Assistant (Optional)
homeassistant:
  url: "http://homeassistant:8123"
  token: "your-long-lived-access-token"

# Data Processing
processing:
  timezone: "Europe/Helsinki"
  min_time_between: 60
```

### Advanced Configuration (`measurements_config.yaml`)
Customize data mappings, validation rules, and processing settings:

```yaml
measurements:
  vitals:
    types: ["HKQuantityTypeIdentifierHeartRate"]
    measurement_name: "heartrate_bpm"
    validation:
      rules:
        value:
          min: 30
          max: 250

global:
  batch_size: 1000
  duplicate_check_window_hours: 24
```

## 📈 Performance

### Benchmarks
| File Size | Processing Time | Memory Usage | Features Used | Improvements |
|-----------|----------------|--------------|---------------|-------------|
| **100 MB** | 2-5 minutes | ~50 MB | Standard mode | ✅ Enhanced parsing |
| **500 MB** | 8-15 minutes | ~200 MB | Auto-streaming | ✅ Better error handling |
| **1+ GB** | 15-25 minutes | ~300 MB | Streaming + checkpoints | ✅ 14k+ elements/sec |
| **3+ GB** | 30-60 minutes | ~400 MB | All optimizations | ✅ Zero validation errors |

### Recent Performance Improvements (2025-08-25)
- **🚀 Processing Speed**: Up to 14k+ elements/second in optimal conditions
- **🛡️ Error Reduction**: Eliminated ~16k validation/parse errors from previous runs
- **🔧 Parser Reliability**: Enhanced datetime parsing with fallback format support
- **💤 Sleep Data Fixed**: Consistent duration units (seconds) for accurate dashboard display

### Memory Efficiency
- **Traditional approach**: File size × 3-4 = RAM usage
- **Our streaming approach**: ~200-500 MB regardless of file size
- **Checkpointing**: Resume from interruption without data loss

## 🔒 Security

### Credential Management
- Store sensitive tokens in `config.yaml` (excluded from Git)
- Use environment variables for production deployments
- Implement proper file permissions (`chmod 600 config.yaml`)
- See [SECURITY.md](SECURITY.md) for comprehensive guidelines

### Best Practices
- Rotate InfluxDB and Home Assistant tokens regularly
- Use dedicated service accounts with minimal permissions
- Monitor access logs for unusual activity
- Enable HTTPS/TLS for all API connections

## 📊 Grafana Visualization

The imported data is optimized for Grafana dashboards:

### Key Metrics Available
- **Heart Rate Trends**: Resting, active, and workout heart rates
- **Activity Tracking**: Daily calories, steps, exercise minutes
- **Sleep Analysis**: Duration, quality scores, sleep patterns
- **Workout Performance**: Distance, duration, energy burned

### Sample Queries
```sql
-- Average heart rate by hour
SELECT mean("value") FROM "heartrate_bpm" 
WHERE time > now() - 7d 
GROUP BY time(1h)

-- Daily calorie summary
SELECT sum("value") FROM "energy_kcal" 
WHERE "energy_type" = 'active' 
GROUP BY time(1d)
```

## 🧪 Testing

### Run Unit Tests
```bash
# Run all tests
python -m pytest

# Run specific test files
python test_health_data_parser.py
python test_influxdb_writer.py

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Test Data Validation
```bash
# Preview import without writing data
python import_health_data.py test_export.xml --preview

# Validate configuration
python -c "from config_manager import ConfigManager; ConfigManager().validate_config()"
```

## 🚨 Troubleshooting

### Common Issues

**Large File Processing**
```bash
# If import is slow or running out of memory
python import_health_data.py export.xml --streaming

# If import was interrupted
python import_health_data.py export.xml --resume
```

**Duplicate Data**
```bash
# Check import history
python import_health_data.py --show-history

# Force clean re-import
python import_health_data.py export.xml --force
```

**Connection Issues**
- Verify InfluxDB is running and accessible
- Check credentials in `config.yaml`
- Test connection: `curl http://your-influxdb:8086/ping`
- Review logs in `import.log`

**Dashboard Query Issues**
```sql
-- Fixed Data Freshness query (InfluxDB compatible)
SELECT last(time) as "Last Data Point" FROM "heart_metrics"

-- Fixed Data Source Statistics (use multiple queries instead of UNION)
SELECT COUNT(*) as "Records", min(time) as "First", max(time) as "Last" FROM "heart_metrics"

-- Fixed Readiness Score (avoid COALESCE, use transforms)
SELECT mean("hrv_sdnn") * 1.2 * 0.4 as "HRV Component" FROM "heart_metrics" WHERE "type" = 'HKQuantityTypeIdentifierHeartRateVariabilitySDNN'
```

### Performance Tuning

**For Very Large Files (>2GB)**
```yaml
# In measurements_config.yaml
global:
  batch_size: 2000          # Larger batches
  performance:
    max_retries: 5          # More retries
    retry_delay_base: 1     # Faster retries
```

**Memory Constrained Environments**
```yaml
global:
  batch_size: 500           # Smaller batches
```

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov

# Run tests before committing
python -m pytest

# Check code quality
python -m flake8 *.py
```

### Adding New Data Types
1. Add type to `measurements_config.yaml`
2. Implement parser method in `health_data_parser.py`
3. Add validation rules in `data_validator.py`
4. Create unit tests
5. Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apple Health for comprehensive health data export
- InfluxDB team for excellent time-series database
- Home Assistant community for smart home integration
- Python community for robust libraries

## 📞 Support

### Getting Help
- **Issues**: [GitHub Issues](https://github.com/mikkomakipaa/apple-health-importer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mikkomakipaa/apple-health-importer/discussions)
- **Documentation**: Check CLAUDE.md for development guidance

### Reporting Bugs
When reporting issues, please include:
- File size and Python version
- Complete error message and stack trace
- Configuration (remove sensitive data)
- Steps to reproduce

---

**⭐ Star this repo if it helps you track your health data!**