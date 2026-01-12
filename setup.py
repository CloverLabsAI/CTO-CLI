#!/usr/bin/env python3
"""Setup script for Worklog CLI."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="worklog-cli",
    version="1.0.0",
    author="Your Name",
    description="A CLI tool to track daily work across Calendar, Chrome, and GitHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/worklog-cli",
    packages=find_packages(),
    py_modules=["worklog", "config"],
    python_requires=">=3.9",
    install_requires=[
        "rich>=13.0.0",
        "requests>=2.28.0",
        "google-api-python-client>=2.100.0",
        "google-auth-httplib2>=0.1.0",
        "google-auth-oauthlib>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "worklog=worklog:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
    ],
)
