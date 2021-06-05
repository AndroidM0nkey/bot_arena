#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'bot-arena-client',
    version = '1.0.0',
    packages = find_packages(),

    # Enable type hints in the installed packages
    package_data = {
        'bot_arena_client': ['bots/*'],
    },

    install_requires = ['bot_arena-proto ~= 1.0.1', 'pygame', 'pyqt5'],

    entry_points = {
        'console_scripts': [
            'bot-arena-client=bot_arena_client.UserInterface:main',
        ],
    }
)
