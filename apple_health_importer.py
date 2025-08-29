#!/usr/bin/env python3
"""
Wrapper script for easy execution of apple-health-importer.
This allows running: python apple_health_importer.py [args]
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from apple_health_importer.main import main

if __name__ == "__main__":
    main()