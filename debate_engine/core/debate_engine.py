#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
import random
import logging
from typing import Dict, List, Optional

from ..orchestrator import RealOrchestrator, DebateState
from ..providers import criar_provedores
from ..config import config
from ..prompt_builder import prompt_builder

logger = logging.getLogger(__name__)


class DebateEngine:
    """
    Facade que encapsula o sistema de debate.
    Fornece uma API pública simples para iniciar, executar e obter resultados.
    """
    
    def __init__(self, providers: Optional[dict] = None, max_rounds: int = None):
        """
        Inicializa o motor de debate.
        
        Args:
            providers: Dicionário de provedores (opcional, se não passar, cria automaticamente).
            max_rounds: Número máximo de rodadas (padrão: config.max_rounds_padrao).
        """
        self.max_rounds = max_rounds or getattr(config, 'max_rounds_padrao', 3)
        self.orchestrator = RealOrchestrator(providers=providers)
        self.state = DebateState()
        self.providers = self.orchestrator.providers
        self.agent_order = self.orchestrator.agent_order
    
    def run_debate(self, tema: str, rodadas: int = None) -> Dict[str, str]:
        """
        Executa um debate completo.
        
        Args:
            tema: O tema do debate.
            rodadas: Número de rodadas (opcional, padrão: self.max_rounds).
        
        Returns:
            Dicionário com as respostas finais de cada agente.
        """
        rodadas = rodadas or self.max_rounds
        respostas_finais = {}
        
        for rodada in range(1, rodadas + 1):
            logger.info(f"Rodada {rodada}...")
            respostas = self.orchestrator.run_round(tema, rodada)
            respostas_finais.update(respostas)
        
        return respostas_finais
    
    def get_resumo(self) -> str:
        """Retorna o resumo do debate."""
        return self.orchestrator.get_debate_summary()
    
    def get_metrics(self) -> dict:
        """Retorna métricas do debate."""
        return self.orchestrator.get_metrics()
    
    def get_historico(self) -> str:
        """Retorna o histórico completo."""
        return self.orchestrator.state.historico
    
    def get_agentes(self) -> List[str]:
        """Retorna a lista de agentes."""
        return self.agent_order
    
    def shutdown(self):
        """Encerra o motor de debate."""
        self.orchestrator.shutdown()