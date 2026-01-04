"""Setup script for Multi-Agent Trading System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="multi-agent-trading",
    version="0.1.0",
    author="ShadySoft",
    author_email="",
    description="Multi-Agent AI Trading System for Forex, Gold, Stocks & Crypto",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shadysoft/multi-agent-trading",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "trading-system=main:main",
        ],
    },
)
