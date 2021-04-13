#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'game_viewer',
    version = '0.1.0',
    packages = find_packages(),

    install_requires = ['bot_arena_proto>=0.2.0', 'pygame'],

    entry_points = {
        'console_scripts': ['game-viewer=game_viewer.main_viewer:main'],
    }
)
