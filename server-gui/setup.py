#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'bot-arena-server-gui',
    version = '1.0.0',
    packages = find_packages(),

    # Enable type hints in the installed packages
    package_data = {
        'bot_arena_server_gui': ['py.typed'],
    },

    install_requires = ['bot-arena-server', 'pygobject'],

    entry_points = {
        'console_scripts': [
            'bot-arena-server-gui=bot_arena_server_gui.__main__:main',
        ],
    }
)
