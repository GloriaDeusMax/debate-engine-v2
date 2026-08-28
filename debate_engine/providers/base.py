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
from ..config import config


class IApiProvider(ABC):
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


class BaseProvider(IApiProvider):
    def __init__(self, nome: str, modelos: List[str], rate_limit: int = 8):
        self._nome = nome
        self._modelos = modelos
        self._modelo_atual = modelos[0] if modelos else ""
        self.rate_limiter = RateLimiter(max_calls_per_minute=rate_limit)
        self.cb = CircuitBreaker(failure_threshold=3, timeout=120)
        self.cache = ResponseCache(
            max_size=getattr(config, 'max_cache_size', 100),
            ttl_seconds=getattr(config, 'cache_ttl', 180)
        )
        self._papel_fixo = ""
    
    def _gerar_cache_key(self, prompt: str) -> str:
        return f"{self._nome}_{hash(prompt[:200])}"
    
    def _executar_com_resiliencia(self, prompt: str, func: Callable, usar_cache: bool = True) -> str:
        if usar_cache:
            cache_key = self._gerar_cache_key(prompt)
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        self.rate_limiter.wait()
        
        if not self.cb.can_execute():
            return f"[Circuit Breaker: {self._nome} indisponível]"
        
        # Implementar retry com backoff progressivo
        max_tentativas = getattr(config, 'max_tentativas', 2)
        backoff_base = getattr(config, 'backoff_base', 3)
        
        for tentativa in range(1, max_tentativas + 1):
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
                self.cb.record_failure(str(e))
                # Se for rate limit, tenta ler Retry-After (se a lib permitir)
                espera = backoff_base * (2 ** (tentativa - 1))  # 3s, 6s, 12s...
                if "429" in str(e) or "rate limit" in str(e).lower():
                    # Tentar extrair Retry-After do erro (se a exceção tiver)
                    retry_after = getattr(e, 'retry_after', None)
                    if retry_after:
                        espera = float(retry_after)
                    print(f"⏳ {self._nome}: rate limit, aguardando {espera:.0f}s (tentativa {tentativa}/{max_tentativas})")
                elif "503" in str(e):
                    print(f"⏳ {self._nome}: serviço indisponível, aguardando {espera:.0f}s")
                else:
                    print(f"⚠️ {self._nome}: erro na chamada, aguardando {espera:.0f}s")
                
                if tentativa < max_tentativas:
                    time.sleep(espera)
                continue
        
        self.cb.record_failure()
        return f"[Erro {self._nome}: Todos os modelos falharam após {max_tentativas} tentativas]"
    
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