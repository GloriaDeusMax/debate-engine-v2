#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque
import time


class RateLimiter:
    """Controla a taxa de requisições para evitar rate limit"""
    
    def __init__(self, max_calls_per_minute=8):
        self.max_calls = max_calls_per_minute
        self.calls = deque()
    
    def wait(self):
        now = time.time()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            sleep_time = 60 - (now - self.calls[0]) + 1
            print(f"⏳ Aguardando {sleep_time:.1f}s (rate limit)...")
            time.sleep(sleep_time)
        self.calls.append(time.time())