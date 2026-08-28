#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
cache.py - Cache de respostas com TTL (Time To Live)

Implementação aprimorada:
- Usa hash SHA-256 para gerar chaves únicas, evitando colisões.
- Estrutura de dados baseada em OrderedDict para controle de ordem (LRU).
- Permite armazenar múltiplas respostas por prompt (com variação de modelo, max_tokens e temperatura).
"""

import time
import hashlib
from typing import Optional, Any
from collections import OrderedDict


class ResponseCache:
    """
    Cache de respostas com TTL (Time To Live).

    Atributos:
        max_size (int): Número máximo de entradas no cache.
        ttl_seconds (int): Tempo de vida padrão das entradas.
        cache (OrderedDict): Dicionário ordenado para controle de acesso LRU.
        hits (int): Contador de acertos no cache.
        misses (int): Contador de erros no cache (quando não encontra).
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Inicializa o cache.

        Args:
            max_size: Número máximo de entradas.
            ttl_seconds: Tempo de vida padrão (segundos).
        """
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _get_key(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """
        Gera uma chave única para o cache usando SHA-256.

        Isso evita colisões e garante que a chave seja determinística.

        Args:
            prompt: O prompt enviado.
            model: O modelo usado.
            max_tokens: Limite de tokens.
            temperature: Temperatura usada.

        Returns:
            str: Chave hash em formato hexadecimal.
        """
        # Combina os parâmetros relevantes
        data = f"{prompt[:500]}:{model}:{max_tokens}:{temperature}"
        # Gera um hash SHA-256
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get(self, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[Any]:
        """
        Obtém uma resposta do cache.

        Args:
            prompt: O prompt original.
            model: O modelo usado.
            max_tokens: Limite de tokens.
            temperature: Temperatura usada.

        Returns:
            A resposta em cache, ou None se não existir/expirar.
        """
        key = self._get_key(prompt, model, max_tokens, temperature)

        if key in self.cache:
            entry = self.cache[key]
            # Verifica se a entrada ainda é válida (TTL)
            if time.time() - entry['timestamp'] < self.ttl:
                self.hits += 1
                # Move para o final (mais recente) para implementar LRU
                self.cache.move_to_end(key)
                return entry['response']
            else:
                # Entrada expirou, remove do cache
                del self.cache[key]

        self.misses += 1
        return None

    def set(self, prompt: str, model: str, max_tokens: int, temperature: float, response: Any) -> None:
        """
        Armazena uma resposta no cache.

        Args:
            prompt: O prompt original.
            model: O modelo usado.
            max_tokens: Limite de tokens.
            temperature: Temperatura usada.
            response: A resposta a ser armazenada.
        """
        key = self._get_key(prompt, model, max_tokens, temperature)

        # Se já existir, remove antes de reinserir (atualiza timestamp)
        if key in self.cache:
            del self.cache[key]

        # Se o cache estiver cheio, remove a entrada mais antiga (LRU)
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)

        # Insere a nova entrada
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }

    def clear(self) -> None:
        """Limpa todo o cache e reseta contadores."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache."""
        total = self.hits + self.misses
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / total if total > 0 else 0.0,
            'size': len(self.cache),
            'max_size': self.max_size
        }


# Instâncias globais (mantidas para compatibilidade)
gemini_cache = ResponseCache(max_size=100, ttl_seconds=180)
groq_cache = ResponseCache(max_size=100, ttl_seconds=180)