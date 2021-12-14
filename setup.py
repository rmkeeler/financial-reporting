"""
Setup file. Run this before using the program for the first time.
pip install -e .

Run that from project root directory. The dot means "everything in current directory."

That tells pip to install all packages directories as packages in (-e) editable
state. So editing the .py files will automatically update the files in the packages.

Example: from definitions import WEBDRIVER_PATH
"""

from setuptools import setup, find_packages

setup(name = 'financial_reporting',
version = '0.1',
packages=find_packages())
