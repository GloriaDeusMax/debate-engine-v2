#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes unitários para provedores (sugestão do Groq)
"""

import pytest
from unittest.mock import Mock, patch

from debate_engine_modular.providers.base import BaseProvider
from debate_engine_modular.providers.gemini import GeminiProvider
from debate_engine_modular.providers.groq import GroqProvider
from debate_engine_modular.providers.nvidia import NvidiaProvider


class TestProviders:
    """Testes para provedores"""
    
    def test_gemini_provider_init(self):
        """Testa inicialização do GeminiProvider"""
        with patch('debate_engine_modular.providers.gemini.genai'):
            provider = GeminiProvider("fake_key")
            assert provider.get_nome() == "gemini"
            assert provider.get_modelo_atual() is not None
    
    def test_groq_provider_init(self):
        """Testa inicialização do GroqProvider"""
        provider = GroqProvider("fake_key")
        assert provider.get_nome() == "groq"
        assert provider.get_modelo_atual() is not None
    
    def test_nvidia_provider_init(self):
        """Testa inicialização do NvidiaProvider"""
        provider = NvidiaProvider("fake_key")
        assert provider.get_nome() == "nvidia"
        assert provider.get_modelo_atual() == "deepseek-ai/deepseek-v4-flash"
    
    def test_base_provider_cache(self):
        """Testa cache do BaseProvider"""
        provider = BaseProvider()
        provider._nome = "test"
        
        # Testa cache
        provider.cache.set("key1", "response1")
        assert provider.cache.get("key1") == "response1"
        
        # Testa TTL
        assert provider.cache.get("key2") is None
    
    def test_base_provider_rate_limiter(self):
        """Testa rate limiter do BaseProvider"""
        provider = BaseProvider()
        provider._nome = "test"
        
        # Testa se o rate limiter existe
        assert provider.rate_limiter is not None
        
        # Testa se o circuit breaker existe
        assert provider.cb is not None

if __name__ == "__main__":
    pytest.main(["-v", __file__])