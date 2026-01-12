from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="geodatahub",
    version="0.1.0",
    author="GeoDataHub Team",
    author_email="info@geodatahub.com",
    description="Unified interface for searching and downloading geospatial data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/geodatahub",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: GIS",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "eodag>=2.9.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
        "api": [
            "fastapi>=0.95.0",
            "uvicorn>=0.20.0",
            "pydantic>=2.0.0",
        ],
        "cli": [
            "click>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "geodatahub=geodatahub.cli:main",
        ],
    },
)
