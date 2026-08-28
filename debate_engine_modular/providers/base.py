#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import List, Optional, Callable

from ..core.rate_limiter import RateLimiter
from ..core.circuit_breaker import CircuitBreaker
from ..core.cache import ResponseCache
from ..utils.clean_response import clean_response


class IApiProvider(ABC):
    """Interface para provedores de LLM (Strategy Pattern)"""
    
    @abstractmethod
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Executa a chamada ao provedor"""
        pass
    
    @abstractmethod
    def get_nome(self) -> str:
        """Retorna o nome do provedor"""
        pass
    
    @abstractmethod
    def get_modelo_atual(self) -> str:
        """Retorna o modelo atual em uso"""
        pass
    
    @abstractmethod
    def get_modelos_disponiveis(self) -> List[str]:
        """Retorna lista de modelos disponíveis"""
        pass


class BaseProvider(IApiProvider):
    """Classe base para provedores com resiliência"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter(max_calls_per_minute=8)
        self.cb = CircuitBreaker(failure_threshold=3, timeout=120)
        self.cache = ResponseCache(max_size=50, ttl_seconds=180)
        self._nome: str = "base"
        self._modelo_atual: str = ""
        self._modelos: List[str] = []
        self._papel_fixo: str = ""
    
    def _gerar_cache_key(self, prompt: str) -> str:
        """Gera chave para o cache"""
        return f"{self._nome}_{hash(prompt[:200])}"
    
    def _executar_com_resiliencia(self, prompt: str, func: Callable, usar_cache: bool = True) -> str:
        """Executa a chamada com Circuit Breaker, Rate Limiter e Cache"""
        
        # 1. Verificar cache
        if usar_cache:
            cache_key = self._gerar_cache_key(prompt)
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # 2. Rate Limiting
        self.rate_limiter.wait()
        
        # 3. Circuit Breaker
        if not self.cb.can_execute():
            return f"[Circuit Breaker: {self._nome} indisponível]"
        
        # 4. Executar a chamada
        try:
            resposta = func()
            if resposta and len(resposta) > 30:
                self.cb.record_success()
                cleaned = clean_response(resposta)
                if usar_cache:
                    self.cache.set(self._gerar_cache_key(prompt), cleaned)
                return cleaned
        except Exception as e:
            print(f"⚠️ {self._nome}: {str(e)[:60]}")
            self.cb.record_failure()
            if "429" in str(e):
                print("⏳ Rate limit, aguardando 10s...")
                time.sleep(10)
            elif "503" in str(e):
                print("⏳ Serviço indisponível, aguardando 5s...")
                time.sleep(5)
            raise
        
        self.cb.record_failure()
        return f"[Erro {self._nome}: Todos os modelos falharam]"
    
    @abstractmethod
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        pass
    
    @abstractmethod
    def get_nome(self) -> str:
        pass
    
    @abstractmethod
    def get_modelo_atual(self) -> str:
        pass
    
    @abstractmethod
    def get_modelos_disponiveis(self) -> List[str]:
        pass