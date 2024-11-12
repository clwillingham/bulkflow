from setuptools import setup, find_packages

# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bulkflow",
    version="0.1.0",
    author="Chris",
    author_email="clwillingham@gmail.com",
    description="A high-performance CSV to PostgreSQL data loader with chunked processing and error handling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clwillingham/bulkflow",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "pandas>=1.0.0,<2.0.0"
    ],
    entry_points={
        'console_scripts': [
            'bulkflow=bulkflow.main:main',
        ],
    },
    keywords="postgresql csv data-loading etl database bulk-import data-processing",
    project_urls={
        "Bug Tracker": "https://github.com/clwillingham/bulkflow/issues",
        "Documentation": "https://github.com/clwillingham/bulkflow",
        "Source Code": "https://github.com/clwillingham/bulkflow",
    },
)
