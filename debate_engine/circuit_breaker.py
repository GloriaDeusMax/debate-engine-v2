#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
circuit_breaker.py - Circuit Breaker para resiliência a falhas

Implementação aprimorada:
- Estados: CLOSED (funcionando), OPEN (bloqueado), HALF_OPEN (testando recuperação).
- Lógica de detecção de falhas baseada em contagem de falhas consecutivas.
- Estratégia de reinicialização automática após timeout (transição OPEN -> HALF_OPEN).
- Registra métricas de chamadas (sucesso, falha, tempo de resposta).
"""

import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class CircuitBreakerState:
    """Estado interno do Circuit Breaker."""
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failures: int = 0
    last_failure_time: float = 0
    last_success_time: float = 0
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0


class CircuitBreaker:
    """
    Circuit Breaker para proteger chamadas a APIs externas.

    Estados:
        CLOSED: Funcionando normalmente.
        OPEN: Bloqueado temporariamente (muitas falhas consecutivas).
        HALF_OPEN: Testando se o serviço se recuperou.
    """

    def __init__(self, name: str = "default", failure_threshold: int = 3, timeout: int = 60):
        """
        Inicializa o Circuit Breaker.

        Args:
            name: Identificador do breaker (para logs).
            failure_threshold: Número de falhas consecutivas para abrir o circuito.
            timeout: Tempo (em segundos) para tentar reinicializar (transição OPEN -> HALF_OPEN).
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.state = CircuitBreakerState()
        self._last_error: Optional[Exception] = None

    def can_execute(self) -> bool:
        """
        Verifica se a chamada pode ser executada.

        Returns:
            True se pode executar, False se deve bloquear (circuito aberto).
        """
        self.state.total_calls += 1

        if self.state.state == "OPEN":
            # Verifica se já passou o timeout para tentar reinicializar
            if time.time() - self.state.last_failure_time > self.timeout:
                self.state.state = "HALF_OPEN"
                self.state.consecutive_failures = 0
                return True
            return False

        # Se CLOSED ou HALF_OPEN, pode executar
        return True

    def record_success(self) -> None:
        """Registra uma chamada bem-sucedida."""
        self.state.successful_calls += 1
        self.state.last_success_time = time.time()
        self.state.consecutive_failures = 0
        self._last_error = None

        if self.state.state == "HALF_OPEN":
            # Se teve sucesso no HALF_OPEN, fecha o circuito completamente
            self.state.state = "CLOSED"
            self.state.failures = 0

    def record_failure(self, error: Optional[Exception] = None) -> None:
        """
        Registra uma falha.

        Args:
            error: A exceção que causou a falha (opcional, para logs).
        """
        self.state.failed_calls += 1
        self.state.consecutive_failures += 1
        self._last_error = error

        # Registra o tempo da última falha
        self.state.last_failure_time = time.time()

        # Verifica se deve abrir o circuito
        if self.state.consecutive_failures >= self.failure_threshold:
            self.state.state = "OPEN"
            self.state.failures = self.state.consecutive_failures

    def reset(self) -> None:
        """Reseta o Circuit Breaker para o estado CLOSED."""
        self.state = CircuitBreakerState()

    def get_status(self) -> dict:
        """Retorna o estado atual para métricas."""
        return {
            'state': self.state.state,
            'consecutive_failures': self.state.consecutive_failures,
            'total_calls': self.state.total_calls,
            'successful_calls': self.state.successful_calls,
            'failed_calls': self.state.failed_calls,
            'last_error': str(self._last_error)[:100] if self._last_error else None
        }


# Instâncias globais (mantidas para compatibilidade)
gemini_cb = CircuitBreaker(name="gemini", failure_threshold=3, timeout=60)
groq_cb = CircuitBreaker(name="groq", failure_threshold=3, timeout=60)