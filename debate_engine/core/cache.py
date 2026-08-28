#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

class ResponseCache:
    def __init__(self, max_size=50, ttl_seconds=180):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                self.hits += 1
                return entry['response']
        self.misses += 1
        return None
    
    def set(self, key, response):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1]['timestamp'])
            del self.cache[oldest[0]]
        self.cache[key] = {'response': response, 'timestamp': time.time()}
    
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0