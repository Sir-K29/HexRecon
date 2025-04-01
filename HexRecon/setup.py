from setuptools import setup, find_packages

setup(
    name="pentest_framework",
    version="0.1.0",
    description="A modular pentesting framework with a plugin architecture.",
    author="Khaled Elarady",
    author_email="elarady.khaled29@gmail.com",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15",
        "rich>=10.0"
    ],
    entry_points={
        "console_scripts": [
            "hexrecon = pentest.main:main",
        ],
    },
)
