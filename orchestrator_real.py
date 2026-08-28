#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
orchestrator_real.py - Orquestrador Refatorado
Versão melhorada com injeção de dependência e estado gerenciado
"""

import os
import time
import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from providers import criar_provedores

# Configurar logging
logger = logging.getLogger(__name__)


@dataclass
class DebateState:
    """Estado do debate - gerenciado centralmente"""
    historico: str = ""
    resumo: str = ""
    falas_rodada: List[tuple] = field(default_factory=list)
    todas_falas: List[tuple] = field(default_factory=list)
    
    def add_fala(self, nome: str, texto: str):
        """Adiciona uma fala ao histórico"""
        self.falas_rodada.append((nome, texto))
        self.todas_falas.append((nome, texto))
        self.historico += f"\n[{nome}]: {texto}\n"
    
    def clear_rodada(self):
        """Limpa as falas da rodada atual"""
        self.falas_rodada = []


class RealOrchestrator:
    """
    Orquestrador refatorado com injeção de dependência.
    """
    
    def __init__(self, providers: Optional[Dict] = None):
        """
        Inicializa o orquestrador.
        
        Args:
            providers: Dicionário de provedores (injeção de dependência)
        """
        # Injeção de dependência ou criação automática
        self.providers = providers if providers is not None else criar_provedores()
        self.agent_order = list(self.providers.keys())
        
        # Modelos para exibição
        self.models = {nome: p.get_modelo() for nome, p in self.providers.items()}
        self.config = {'debate': {'max_rounds': 3}}
        
        # Estado do debate (agora com dataclass)
        self.state = DebateState()
        
        if self.agent_order:
            logger.info(f"Agentes: {', '.join(self.agent_order)}")
        else:
            logger.error("Nenhum agente disponível!")
    
    def run_round(self, tema: str, rodada: int) -> Dict[str, str]:
        """Executa uma rodada usando Strategy Pattern."""
        if not self.agent_order:
            return {"Erro": "Nenhum agente disponível"}
        
        respostas = {}
        ordem = self.agent_order.copy()
        random.shuffle(ordem)
        
        for nome in ordem:
            provider = self.providers.get(nome)
            if not provider:
                continue
            
            logger.info(f"💭 {nome} pensando...")
            
            # Criar prompt específico
            prompt = self._criar_prompt(nome, tema)
            
            try:
                resposta = provider.gerar_resposta(prompt)
                
                if resposta.startswith("[Erro"):
                    logger.warning(f"⚠️ {nome} retornou erro: {resposta[:80]}...")
                else:
                    logger.info(f"✅ {nome} respondeu com sucesso!")
                    
            except Exception as e:
                resposta = f"[Erro inesperado em {nome}: {str(e)[:100]}]"
                logger.error(f"❌ {nome} falhou: {str(e)[:80]}")
            
            # Adicionar ao estado
            self.state.add_fala(nome, resposta)
            respostas[nome] = resposta
            time.sleep(1)  # Evitar rate limit
        
        # Limpar rodada (mantém o histórico)
        self.state.clear_rodada()
        
        return respostas
    
    def _criar_prompt(self, agente: str, tema: str) -> str:
        """Cria prompt específico para cada agente."""
        tema_limitado = tema[:3500] if len(tema) > 3500 else tema
        
        prompts = {
            'gemini': f"""Você é um especialista em arquitetura de software.
Analise este código e dê sugestões de melhoria.

{tema_limitado}

Responda em português do Brasil, de forma concisa e prática.
Dê sugestões específicas baseadas no código apresentado.
""",
            'groq': f"""Você é um engenheiro de software Python.
Analise este código e dê sugestões práticas.

{tema_limitado}

Responda em português do Brasil, de forma concisa e com exemplos práticos.
"""
        }
        return prompts.get(agente, tema_limitado)
    
    def get_debate_summary(self) -> str:
        """Retorna o resumo do debate."""
        if not self.state.historico:
            return "Nenhum histórico disponível."
        historico = self.state.historico
        return historico[-500:] if len(historico) > 500 else historico
    
    def get_metrics(self) -> Dict:
        """Retorna métricas do debate."""
        return {
            'agentes': self.agent_order,
            'models': {nome: p.get_modelo() for nome, p in self.providers.items()},
            'total_respostas': len(self.state.todas_falas),
            'provedores_ativos': len(self.providers)
        }


if __name__ == "__main__":
    orchestrator = RealOrchestrator()
    if orchestrator.providers:
        from debate_engine_ui import DebateUI
        ui = DebateUI(orchestrator)
        ui.run()