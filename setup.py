#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="apple-health-importer",
    version="1.0.0",
    author="Mikko Mäkipää",
    author_email="mikko.makipaa@example.com",
    description="Import Apple Health data to InfluxDB with comprehensive validation and processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mikkomakipaa/apple-health-importer",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "flake8",
            "black",
            "mypy",
            "pre-commit",
        ],
    },
    entry_points={
        "console_scripts": [
            "apple-health-importer=apple_health_importer.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)