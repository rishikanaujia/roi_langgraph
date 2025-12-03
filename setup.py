from setuptools import setup, find_packages

setup(
    name="roi-poc",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0.1",
    ],
)