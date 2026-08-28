#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
exceptions.py - Exceções customizadas do 4KINGS Debate Engine
"""


class DebateEngineError(Exception):
    """Exceção base para o 4KINGS Debate Engine."""
    pass


class EnvironmentError(DebateEngineError):
    """Erro relacionado ao ambiente (dependências, chaves, pastas)."""
    pass


class ConfigurationError(EnvironmentError):
    """Erro de configuração (arquivo .env, config.yaml)."""
    pass


class OrchestratorError(DebateEngineError):
    """Erro relacionado ao orquestrador."""
    pass


class ProviderError(DebateEngineError):
    """Erro relacionado aos provedores de LLM."""
    pass


class ProviderNotFoundError(ProviderError):
    """Provedor não encontrado."""
    pass


class ProviderConnectionError(ProviderError):
    """Erro de conexão com o provedor."""
    pass


class CircuitBreakerOpenError(DebateEngineError):
    """Circuit Breaker está aberto - provedor indisponível."""
    pass


class RateLimitError(DebateEngineError):
    """Rate limit excedido."""
    pass


class CacheError(DebateEngineError):
    """Erro relacionado ao cache."""
    pass


class TokenLimitError(DebateEngineError):
    """Limite de tokens excedido."""
    pass


class UIError(DebateEngineError):
    """Erro relacionado à interface de usuário."""
    pass