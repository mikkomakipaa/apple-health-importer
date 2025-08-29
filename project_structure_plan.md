# Project Reorganization Plan

## Current Structure Issues
- Core Python modules mixed with config files in root
- Test files scattered in root directory  
- Documentation files mixed with source code
- No clear separation of concerns
- Missing standard GitHub project files

## Proposed GitHub-Friendly Structure

```
apple-health-importer/
├── README.md                          # Main project documentation
├── LICENSE                           # License file
├── .gitignore                       # Git ignore patterns
├── requirements.txt                 # Python dependencies
├── setup.py                        # Package setup (NEW)
├── pyproject.toml                   # Modern Python project config (NEW)
│
├── .github/                         # GitHub-specific files (NEW)
│   ├── workflows/                   # GitHub Actions CI/CD
│   │   ├── ci.yml                  # Continuous integration
│   │   └── security.yml            # Security scanning
│   ├── ISSUE_TEMPLATE/              # Issue templates
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── PULL_REQUEST_TEMPLATE.md     # PR template
│   └── CODEOWNERS                   # Code ownership
│
├── src/                            # Source code (NEW)
│   └── apple_health_importer/       # Main package
│       ├── __init__.py
│       ├── main.py                  # Entry point (renamed from import_health_data.py)
│       ├── config/                  # Configuration modules
│       │   ├── __init__.py
│       │   ├── manager.py           # config_manager.py
│       │   └── enhanced.py          # enhanced_config.py
│       ├── parsers/                 # Data parsing modules
│       │   ├── __init__.py
│       │   ├── health_data.py       # health_data_parser.py
│       │   └── streaming.py         # streaming_processor.py
│       ├── writers/                 # Data output modules
│       │   ├── __init__.py
│       │   ├── influxdb.py          # influxdb_writer.py
│       │   └── homeassistant.py     # homeassistant.py
│       ├── validation/              # Data validation
│       │   ├── __init__.py
│       │   └── validator.py         # data_validator.py
│       ├── tracking/                # Import tracking
│       │   ├── __init__.py
│       │   └── tracker.py           # import_tracker.py
│       └── utils/                   # Utilities
│           ├── __init__.py
│           └── performance.py       # performance_optimizer.py
│
├── tests/                          # Test files (NEW structure)
│   ├── __init__.py
│   ├── conftest.py                 # pytest configuration
│   ├── unit/                       # Unit tests
│   │   ├── test_health_data_parser.py
│   │   ├── test_influxdb_writer.py
│   │   └── test_panel_queries.py
│   ├── integration/                # Integration tests
│   └── fixtures/                   # Test data
│       └── sample_export.xml
│
├── config/                         # Configuration files
│   ├── config.yaml.example
│   ├── measurements_config.yaml
│   └── measurements_config_comprehensive.yaml
│
├── scripts/                        # Deployment and utility scripts
│   ├── secure_deploy.sh
│   └── grafana_sleep_queries_fixed.sql
│
├── docs/                           # Documentation
│   ├── index.md                    # Documentation index
│   ├── installation.md             # Installation guide
│   ├── configuration.md            # Configuration guide
│   ├── deployment.md               # Deployment guide (from deployment_guide.md)
│   ├── security.md                 # Security guide (from security_improvements.md)
│   ├── performance.md              # Performance analysis (from final_swarm_report.md)
│   ├── troubleshooting.md          # Troubleshooting guide
│   ├── sleep-data-analysis.md      # Sleep data analysis
│   └── api/                        # API documentation
│
├── examples/                       # Usage examples
│   ├── basic_import.py
│   ├── advanced_config.py
│   └── sample_data/
│       └── sample_export.xml
│
├── dashboards/                     # Grafana dashboards (NEW)
│   ├── Apple Health Ultimate Dashboard.json
│   └── sleep_queries.sql
│
└── tools/                          # Development tools (NEW)
    ├── dev_requirements.txt        # Development dependencies
    └── lint.sh                     # Code quality tools
```

## Benefits of This Structure
1. **Clear separation of concerns**: Source, tests, docs, config
2. **Standard Python package structure**: Easy to install and distribute
3. **GitHub best practices**: Issue templates, workflows, CODEOWNERS
4. **Professional appearance**: Looks like a mature, well-maintained project
5. **Easy navigation**: Users can quickly find what they need
6. **CI/CD ready**: GitHub Actions workflows for automated testing
7. **Package-ready**: Can be published to PyPI if desired

## Migration Plan
1. Create new directory structure
2. Move files to appropriate locations
3. Update import statements
4. Create GitHub-specific files
5. Update documentation references
6. Test that everything still works
7. Update README with new structure