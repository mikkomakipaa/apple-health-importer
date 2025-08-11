# Security Guidelines

## Credential Management

### Configuration File Security

The `config.yaml` file contains sensitive credentials including:
- InfluxDB authentication tokens
- Home Assistant access tokens

**Important Security Practices:**

1. **File Permissions**: Restrict access to configuration files
   ```bash
   chmod 600 config.yaml
   ```

2. **Never Commit Credentials**: Add config files to `.gitignore`
   ```bash
   echo "config.yaml" >> .gitignore
   ```

3. **Environment Variables**: Consider using environment variables for production:
   ```bash
   export INFLUXDB_TOKEN="your-token"
   export HOMEASSISTANT_TOKEN="your-token"
   ```

4. **Backup Security**: If backing up config files, ensure backups are encrypted

### Recommended Secure Setup

1. **Use dedicated service accounts** with minimal required permissions
2. **Rotate tokens regularly** (quarterly recommended)
3. **Monitor access logs** for unusual activity
4. **Use HTTPS/TLS** for all API connections
5. **Store config files outside the project directory** in production

### Token Permissions

**InfluxDB Token Permissions:**
- Read/Write access to the health data bucket only
- No admin permissions required

**Home Assistant Token:**
- States read/write permission
- No config or admin access needed

## Network Security

- All API calls use HTTPS by default
- Validate SSL certificates in production
- Consider using VPN or private networks for internal services

## Data Privacy

- Health data is sensitive personal information
- Ensure compliance with local privacy regulations (GDPR, HIPAA, etc.)
- Consider data retention policies
- Implement proper data deletion procedures when needed