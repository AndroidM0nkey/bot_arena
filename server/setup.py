#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'bot-arena-server',
    version = '0.1.0-a',
    packages = find_packages(),

    # Enable type hints in the installed package
    package_data = {'bot_arena_server': ['py.typed']},

    install_requires = ['bot-arena-proto', 'curio'],

    entry_points = {
        'console_scripts': ['bot-arena-server=bot_arena_server.__main__:main'],
    }
)
