#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
interfaces.py - Interfaces abstratas do 4KINGS Debate Engine
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class OrchestratorInterface(ABC):
    """Interface para orquestradores de debate."""
    
    @abstractmethod
    def run_round(self, tema: str, rodada: int) -> Dict[str, str]:
        """Executa uma rodada do debate."""
        pass
    
    @abstractmethod
    def get_debate_summary(self) -> str:
        """Retorna o resumo do debate."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict:
        """Retorna métricas do debate."""
        pass


class LLMProviderInterface(ABC):
    """Interface para provedores de LLM."""
    
    @abstractmethod
    def gerar_resposta(self, prompt: str, max_tokens: int = 400, usar_cache: bool = True) -> str:
        """Gera uma resposta do modelo."""
        pass
    
    @abstractmethod
    def get_nome(self) -> str:
        """Retorna o nome do provedor."""
        pass
    
    @abstractmethod
    def get_modelo(self) -> str:
        """Retorna o modelo atual em uso."""
        pass


class CacheInterface(ABC):
    """Interface para cache de respostas."""
    
    @abstractmethod
    def get(self, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[Any]:
        """Obtém uma resposta do cache."""
        pass
    
    @abstractmethod
    def set(self, prompt: str, model: str, max_tokens: int, temperature: float, response: Any) -> None:
        """Armazena uma resposta no cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Limpa o cache."""
        pass


class MetricsInterface(ABC):
    """Interface para coleta de métricas."""
    
    @abstractmethod
    def record_api_call(self, provider: str, model: str, success: bool, 
                        response_time: float, tokens: int = 0, error: Optional[str] = None) -> None:
        """Registra uma chamada de API."""
        pass
    
    @abstractmethod
    def get_summary(self) -> Dict:
        """Retorna um resumo das métricas."""
        pass