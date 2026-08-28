#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
metrics.py - Coleta de métricas
"""

import time
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional


class MetricsCollector:
    """Coleta métricas do sistema"""
    
    def __init__(self):
        self.metrics = {
            'debates': [],
            'api_calls': defaultdict(list),
            'errors': defaultdict(int),
            'tokens_used': defaultdict(int),
            'response_times': defaultdict(list),
        }
        self.start_time = time.time()
    
    def record_debate(self, tema: str, rounds: int, messages: int):
        """Registra um debate completo."""
        self.metrics['debates'].append({
            'tema': tema,
            'rounds': rounds,
            'messages': messages,
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - self.start_time,
        })
    
    def record_api_call(self, provider: str, model: str, success: bool, 
                        response_time: float, tokens: int = 0, error: Optional[str] = None):
        """Registra uma chamada de API."""
        self.metrics['api_calls'][provider].append({
            'model': model,
            'success': success,
            'response_time': response_time,
            'tokens': tokens,
            'error': error,
            'timestamp': datetime.now().isoformat(),
        })
        
        if not success:
            self.metrics['errors'][provider] += 1
        
        self.metrics['tokens_used'][provider] += tokens
        self.metrics['response_times'][provider].append(response_time)
    
    def get_summary(self) -> dict:
        """Retorna um resumo das métricas."""
        total_api_calls = sum(len(calls) for calls in self.metrics['api_calls'].values())
        total_errors = sum(self.metrics['errors'].values())
        
        return {
            'total_debates': len(self.metrics['debates']),
            'total_api_calls': total_api_calls,
            'total_errors': total_errors,
            'error_rate': (total_errors / total_api_calls * 100) if total_api_calls > 0 else 0,
            'uptime_seconds': time.time() - self.start_time,
            'providers': dict(self.metrics['tokens_used']),
            'avg_response_time': {
                provider: sum(times) / len(times) if times else 0
                for provider, times in self.metrics['response_times'].items()
            },
            'recent_debates': self.metrics['debates'][-5:] if self.metrics['debates'] else [],
        }
    
    def get_provider_metrics(self, provider: str) -> dict:
        """Retorna métricas de um provedor específico."""
        calls = self.metrics['api_calls'].get(provider, [])
        if not calls:
            return {}
        
        successes = [c for c in calls if c['success']]
        return {
            'total_calls': len(calls),
            'successful': len(successes),
            'failed': len(calls) - len(successes),
            'success_rate': (len(successes) / len(calls) * 100) if calls else 0,
            'avg_response_time': sum(c['response_time'] for c in calls) / len(calls) if calls else 0,
            'total_tokens': self.metrics['tokens_used'].get(provider, 0),
            'errors': self.metrics['errors'].get(provider, 0),
        }


# Instância global
metrics = MetricsCollector()