#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
4KINGS Debate Engine - Pacote modular com Strategy Pattern
"""

from .interfaces import IApiProvider, IOrchestrator, IProviderFactory
from .providers import GeminiProvider, GroqProvider, OpenRouterProvider, ProviderFactory
from .main import DebateEngine, DebateUI, main

__all__ = [
    'IApiProvider',
    'IOrchestrator',
    'IProviderFactory',
    'GeminiProvider',
    'GroqProvider',
    'OpenRouterProvider',
    'ProviderFactory',
    'DebateEngine',
    'DebateUI',
    'main',
]