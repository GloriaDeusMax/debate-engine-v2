#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from core.rate_limiter import RateLimiter
from core.circuit_breaker import CircuitBreaker
from core.cache import ResponseCache
from utils.clean_response import clean_response


def call_gemini(client, prompt, papel, modelos, max_tokens=800, temperature=0.3):
    rate_limiter = RateLimiter(max_calls_per_minute=5)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    cache = ResponseCache(max_size=50, ttl_seconds=180)
    
    cache_key = f"gemini_{hash(prompt[:200])}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: Gemini indisponível]"
    
    for modelo in modelos:
        try:
            print(f"🔄 Tentando Gemini: {modelo}")
            response = client.models.generate_content(
                model=modelo,
                contents=f"{papel}\n\n{prompt}"
            )
            if response.text and len(response.text) > 30:
                cb.record_success()
                cleaned = clean_response(response.text)
                cache.set(cache_key, cleaned)
                return cleaned
        except Exception as e:
            print(f"⚠️ Gemini ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                print("⏳ Rate limit, aguardando 10s...")
                time.sleep(10)
            elif "503" in str(e):
                print("⏳ Serviço indisponível, aguardando 5s...")
                time.sleep(5)
            continue
    
    cb.record_failure()
    return "[Erro Gemini: Todos os modelos falharam]"