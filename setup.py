#!/usr/bin/env python3
# encoding:utf-8
"""
WEDBRIDGE - 企业微信 + Dify 智能桥接平台
一键安装后即可使用 wedbridge 命令
"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

# 读取 README
readme_path = os.path.join(here, "docs", "README.md")
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "WEDBRIDGE - 企业微信 + Dify 智能桥接平台"

setup(
    name="wedbridge",
    version="1.0.0",
    description="WEDBRIDGE - 企业微信 + Dify 智能桥接平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="WEDBRIDGE Team",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "bridge": ["../../core/*.py", "../../config/*.json", "../../scripts/*"],
    },
    install_requires=[
        "wecom-aibot-sdk-python>=0.1.0",
        "aiohttp>=3.8.0",
        'dataclasses; python_version<"3.8"',
        'typing-extensions>=4.0.0; python_version<"3.10"',
    ],
    entry_points={
        "console_scripts": [
            "wedbridge=bridge.cli:main",
            "wb=bridge.cli:main",  # 简写别名
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
