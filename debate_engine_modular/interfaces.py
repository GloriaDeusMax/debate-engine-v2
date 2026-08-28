#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IApiProvider(ABC):
    """Interface abstrata para provedores de LLM (Strategy Pattern)"""
    
    @abstractmethod
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Executa a chamada ao provedor"""
        pass
    
    @abstractmethod
    def get_nome(self) -> str:
        """Retorna o nome do provedor"""
        pass
    
    @abstractmethod
    def get_modelo_atual(self) -> str:
        """Retorna o modelo atual em uso"""
        pass
    
    @abstractmethod
    def get_modelos_disponiveis(self) -> List[str]:
        """Retorna lista de modelos disponíveis"""
        pass


class IOrchestrator(ABC):
    """Interface para orquestradores de debate"""
    
    @abstractmethod
    def run_round(self, tema: str, rodada: int) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def get_debate_summary(self) -> str:
        pass
    
    @abstractmethod
    def get_metrics(self) -> Dict:
        pass