#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'bot-arena-server',
    version = '1.0.0',
    packages = find_packages(),

    # Enable type hints in the installed packages
    package_data = {
        'bot_arena_server': ['py.typed'],
    },

    install_requires = ['bot-arena-proto ~= 1.0.1', 'curio', 'loguru'],

    entry_points = {
        'console_scripts': [
            'bot-arena-server=bot_arena_server.__main__:main',
        ],
    }
)
