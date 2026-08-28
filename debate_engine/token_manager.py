#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
token_manager.py - Gerenciamento de tokens
"""

import re
import threading
from typing import Optional


class TokenManager:
    """Gerencia o uso de tokens para evitar estouro de contexto"""
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.used_tokens = 0
        self.lock = threading.Lock()
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto.
        Aproximação para português: ~1.3 tokens por palavra.
        """
        if not text:
            return 0
        
        # Contar palavras
        words = len(re.findall(r'\w+', text))
        # Contar pontuação
        punctuation = len(re.findall(r'[.!?;,:]', text))
        # Contar caracteres especiais
        special = len(re.findall(r'[^a-zA-Z0-9áéíóúãõç\s.!?;,:]', text))
        
        return int(words * 1.3 + punctuation * 0.5 + special * 0.3 + 5)
    
    def can_afford(self, text: str) -> bool:
        """Verifica se cabe mais texto no contexto."""
        with self.lock:
            estimated = self.estimate_tokens(text)
            return (self.used_tokens + estimated) < self.max_tokens
    
    def consume_tokens(self, text: str) -> int:
        """Consome tokens e retorna a quantidade consumida."""
        with self.lock:
            estimated = self.estimate_tokens(text)
            self.used_tokens += estimated
            return estimated
    
    def reset(self):
        """Reseta o contador de tokens."""
        with self.lock:
            self.used_tokens = 0
    
    def get_usage(self) -> dict:
        """Retorna o uso atual de tokens."""
        with self.lock:
            return {
                'used': self.used_tokens,
                'max': self.max_tokens,
                'percent': (self.used_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0
            }
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trunca o texto para caber no limite de tokens."""
        if self.estimate_tokens(text) <= max_tokens:
            return text
        
        # Truncar por palavras
        words = text.split()
        result = []
        current_tokens = 0
        
        for word in words:
            word_tokens = self.estimate_tokens(word)
            if current_tokens + word_tokens > max_tokens:
                break
            result.append(word)
            current_tokens += word_tokens
        
        return ' '.join(result) + "..."


# Instância global
token_manager = TokenManager(max_tokens=8000)