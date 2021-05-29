#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = 'bot_arena_proto',
    version = '1.0.0',
    packages = find_packages(),

    # Enable type hints in the installed package
    package_data = {'bot_arena_proto': ['py.typed']},

    install_requires = ['algebraic_data_types', 'cbor2', 'curio'],
)
