#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
rate_limiter.py - Rate Limiting para chamadas de API
"""

import time
import threading
from collections import deque


class RateLimiter:
    """Controla a taxa de requisições para APIs"""
    
    def __init__(self, max_calls_per_minute: int = 10):
        self.max_calls = max_calls_per_minute
        self.calls = deque()
        self.lock = threading.Lock()
    
    def wait(self):
        """
        Espera se necessário para respeitar o rate limit.
        Bloqueia até que seja seguro fazer a chamada.
        """
        with self.lock:
            now = time.time()
            # Remove chamadas antigas
            while self.calls and now - self.calls[0] > 60:
                self.calls.popleft()
            
            if len(self.calls) >= self.max_calls:
                sleep_time = 60 - (now - self.calls[0]) + 0.5
                time.sleep(sleep_time)
                # Atualiza o timestamp após a espera
                now = time.time()
                while self.calls and now - self.calls[0] > 60:
                    self.calls.popleft()
            
            self.calls.append(time.time())
    
    def get_usage(self) -> dict:
        """Retorna o uso atual do rate limiter."""
        with self.lock:
            now = time.time()
            while self.calls and now - self.calls[0] > 60:
                self.calls.popleft()
            
            return {
                'current_calls': len(self.calls),
                'max_calls': self.max_calls,
                'usage_percent': (len(self.calls) / self.max_calls * 100) if self.max_calls > 0 else 0
            }