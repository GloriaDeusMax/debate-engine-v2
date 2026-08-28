#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .main import main
from .core.debate_engine import DebateEngine
from .providers import criar_provedores, GeminiProvider, GroqProvider, OpenRouterProvider, NvidiaProvider, OllamaProvider

__all__ = [
    "main",
    "DebateEngine",
    "criar_provedores",
    "GeminiProvider",
    "GroqProvider",
    "OpenRouterProvider",
    "NvidiaProvider",
    "OllamaProvider",
]