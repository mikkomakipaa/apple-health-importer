#!/bin/bash
set -euo pipefail

# Apple Health Importer - Secure Deployment Script
# This script implements security best practices for production deployment

echo "🔒 Apple Health Importer - Secure Deployment"
echo "=============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Error: This script should not be run as root${NC}"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Function to print colored status messages
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check required environment variables
check_env_vars() {
    echo "Checking required environment variables..."
    
    required_vars=("INFLUXDB_URL" "INFLUXDB_TOKEN" "HOMEASSISTANT_URL" "HOMEASSISTANT_TOKEN")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        echo ""
        echo "Please set these variables in your environment:"
        echo "export INFLUXDB_URL='https://your-influxdb:8086'"
        echo "export INFLUXDB_TOKEN='your-secure-token'"
        echo "export HOMEASSISTANT_URL='https://your-ha:8123'"
        echo "export HOMEASSISTANT_TOKEN='your-ha-token'"
        exit 1
    fi
    
    print_status "All required environment variables are set"
}

# Create secure configuration
create_secure_config() {
    echo "Creating secure configuration..."
    
    # Create config directory if it doesn't exist
    mkdir -p ~/.apple_health_importer
    
    # Generate config file with environment variables
    cat > ~/.apple_health_importer/config.yaml << EOF
# Apple Health Importer Configuration
# Generated: $(date)

influxdb:
  url: "${INFLUXDB_URL}"
  token: "${INFLUXDB_TOKEN}"
  org: "${INFLUXDB_ORG:-default}"
  bucket: "${INFLUXDB_BUCKET:-apple_health}"

homeassistant:
  url: "${HOMEASSISTANT_URL}"
  token: "${HOMEASSISTANT_TOKEN}"

processing:
  timezone: "${TIMEZONE:-UTC}"
  min_time_between: 60

logging:
  level: "${LOG_LEVEL:-INFO}"
  file: "${LOG_FILE:-/var/log/apple_health_importer.log}"

security:
  max_file_size_mb: 1024
  allowed_extensions: [".xml"]
  enable_audit_log: true
EOF

    # Set secure permissions
    chmod 600 ~/.apple_health_importer/config.yaml
    print_status "Secure configuration created at ~/.apple_health_importer/config.yaml"
}

# Set up logging directory
setup_logging() {
    echo "Setting up secure logging..."
    
    # Create log directory
    sudo mkdir -p /var/log/apple_health_importer
    
    # Set ownership and permissions
    sudo chown $USER:$USER /var/log/apple_health_importer
    chmod 750 /var/log/apple_health_importer
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/apple_health_importer > /dev/null << EOF
/var/log/apple_health_importer/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    postrotate
        systemctl restart apple_health_importer || true
    endscript
}
EOF
    
    print_status "Logging configured with rotation"
}

# Install Python dependencies in virtual environment
install_dependencies() {
    echo "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        print_status "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Install security scanning tools
    pip install safety bandit
    
    print_status "Dependencies installed in virtual environment"
}

# Run security scans
run_security_scans() {
    echo "Running security scans..."
    
    source venv/bin/activate
    
    # Check for known security vulnerabilities
    echo "Checking for vulnerable dependencies..."
    safety check --json > security_scan.json || true
    
    # Run static security analysis
    echo "Running static security analysis..."
    bandit -r . -f json -o bandit_report.json -x "venv/*,tests/*" || true
    
    print_status "Security scans completed"
}

# Create systemd service
create_systemd_service() {
    echo "Creating systemd service..."
    
    # Get current directory
    current_dir=$(pwd)
    
    sudo tee /etc/systemd/system/apple-health-importer.service > /dev/null << EOF
[Unit]
Description=Apple Health Data Importer
After=network.target
Wants=network.target

[Service]
Type=oneshot
User=$USER
Group=$USER
WorkingDirectory=$current_dir
Environment=PATH=$current_dir/venv/bin
ExecStart=$current_dir/venv/bin/python import_health_data.py --config ~/.apple_health_importer/config.yaml
StandardOutput=journal
StandardError=journal
SyslogIdentifier=apple-health-importer

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/log/apple_health_importer
RestrictRealtime=yes
RestrictNamespaces=yes

[Install]
WantedBy=multi-user.target
EOF
    
    # Create timer for scheduled imports
    sudo tee /etc/systemd/system/apple-health-importer.timer > /dev/null << EOF
[Unit]
Description=Run Apple Health Importer daily
Requires=apple-health-importer.service

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable apple-health-importer.timer
    
    print_status "Systemd service and timer created"
}

# Setup monitoring
setup_monitoring() {
    echo "Setting up monitoring..."
    
    # Create monitoring script
    cat > monitor_health_import.sh << 'EOF'
#!/bin/bash
# Health Import Monitor Script

LOG_FILE="/var/log/apple_health_importer/import.log"
ERROR_LOG="/var/log/apple_health_importer/errors.log"
WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

check_last_run() {
    if [[ -f "$LOG_FILE" ]]; then
        last_run=$(tail -n 1 "$LOG_FILE" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}')
        today=$(date +%Y-%m-%d)
        
        if [[ "$last_run" != "$today" ]]; then
            echo "WARNING: Last successful import was on $last_run, not today ($today)"
            return 1
        fi
    else
        echo "ERROR: No log file found at $LOG_FILE"
        return 1
    fi
    
    return 0
}

check_errors() {
    if [[ -f "$ERROR_LOG" ]]; then
        error_count=$(wc -l < "$ERROR_LOG")
        if [[ $error_count -gt 0 ]]; then
            echo "WARNING: $error_count errors found in error log"
            return 1
        fi
    fi
    
    return 0
}

send_alert() {
    local message="$1"
    
    if [[ -n "$WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Apple Health Importer Alert: $message\"}" \
            "$WEBHOOK_URL"
    fi
    
    logger -t apple-health-monitor "$message"
}

main() {
    if ! check_last_run; then
        send_alert "Import service may not be running correctly"
        exit 1
    fi
    
    if ! check_errors; then
        send_alert "Errors detected in import process"
        exit 1
    fi
    
    echo "Health import monitoring: All checks passed"
}

main "$@"
EOF
    
    chmod +x monitor_health_import.sh
    
    # Add monitoring to crontab
    (crontab -l 2>/dev/null; echo "0 */6 * * * $PWD/monitor_health_import.sh") | crontab -
    
    print_status "Monitoring configured"
}

# Backup and restore functions
setup_backup() {
    echo "Setting up backup procedures..."
    
    mkdir -p backups
    
    cat > backup_config.sh << 'EOF'
#!/bin/bash
# Configuration Backup Script

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp ~/.apple_health_importer/config.yaml "$BACKUP_DIR/"

# Backup logs
cp -r /var/log/apple_health_importer "$BACKUP_DIR/"

# Create backup archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"

# Keep only last 7 days of backups
find backups/ -name "*.tar.gz" -mtime +7 -delete
EOF
    
    chmod +x backup_config.sh
    print_status "Backup procedures configured"
}

# Main deployment function
main() {
    echo "Starting secure deployment..."
    echo ""
    
    check_env_vars
    echo ""
    
    create_secure_config
    echo ""
    
    setup_logging
    echo ""
    
    install_dependencies
    echo ""
    
    run_security_scans
    echo ""
    
    create_systemd_service
    echo ""
    
    setup_monitoring
    echo ""
    
    setup_backup
    echo ""
    
    print_status "Secure deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start the timer: sudo systemctl start apple-health-importer.timer"
    echo "2. Check status: systemctl status apple-health-importer.timer"
    echo "3. View logs: journalctl -u apple-health-importer -f"
    echo "4. Run manual import: ./venv/bin/python import_health_data.py export.xml"
    echo ""
    echo "Security recommendations:"
    echo "- Regularly update dependencies: pip install --upgrade -r requirements.txt"
    echo "- Monitor logs for unusual activity"
    echo "- Rotate API tokens quarterly"
    echo "- Review security scan reports in security_scan.json and bandit_report.json"
}

# Run main function
main "$@"