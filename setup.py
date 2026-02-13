"""Setup configuration for AI Governance Tool."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-governance",
    version="0.1.0",
    author="AI Governance Tool",
    description="Secure AI-assisted code refactoring with policy controls",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-governance-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "anthropic>=0.18.0",
        "click>=8.1.0",
        "pyyaml>=6.0",
        "colorama>=0.4.6",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ai-governance=ai_governance.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "ai_governance": ["profiles/*.yaml"],
    },
)
