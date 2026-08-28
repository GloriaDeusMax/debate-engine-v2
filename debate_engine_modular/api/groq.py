#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from core.rate_limiter import RateLimiter
from core.circuit_breaker import CircuitBreaker
from core.cache import ResponseCache
from utils.clean_response import clean_response


def call_groq(client, prompt, papel, modelos, max_tokens=800, temperature=0.3):
    rate_limiter = RateLimiter(max_calls_per_minute=8)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    cache = ResponseCache(max_size=50, ttl_seconds=180)
    
    cache_key = f"groq_{hash(prompt[:200])}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: Groq indisponível]"
    
    for modelo in modelos:
        try:
            print(f"🔄 Tentando Groq: {modelo}")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            content = response.choices[0].message.content
            if content and len(content) > 20:
                cb.record_success()
                cleaned = clean_response(content)
                cache.set(cache_key, cleaned)
                return cleaned
        except Exception as e:
            print(f"⚠️ Groq ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                print("⏳ Rate limit, aguardando 10s...")
                time.sleep(10)
            continue
    
    cb.record_failure()
    return "[Erro Groq: Todos os modelos falharam]"