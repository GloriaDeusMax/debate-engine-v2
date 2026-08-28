#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import time
import random
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict

from .interfaces import OrchestratorInterface
from .providers import criar_provedores
from .cache import ResponseCache
from .config import config
from .metrics import metrics
from .exceptions import ProviderError, CacheError
from .prompt_builder import prompt_builder

logger = logging.getLogger(__name__)


@dataclass
class DebateState:
    historico: str = ""
    resumo: str = ""
    falas_rodada: list[tuple] = field(default_factory=list)
    todas_falas: list[tuple] = field(default_factory=list)
    
    def add_fala(self, nome: str, texto: str) -> None:
        self.falas_rodada.append((nome, texto))
        self.todas_falas.append((nome, texto))
        self.historico += f"\n[{nome}]: {texto}\n"
    
    def clear_rodada(self) -> None:
        self.falas_rodada = []


class RealOrchestrator(OrchestratorInterface):
    def __init__(self, providers: Optional[dict] = None, config_obj=None, metrics_obj=None):
        self._initialized = False
        self.config = config_obj if config_obj is not None else config
        self.metrics = metrics_obj if metrics_obj is not None else metrics
        
        try:
            self.providers = providers if providers is not None else criar_provedores()
        except Exception as e:
            raise ProviderError(f"Erro ao criar provedores: {e}")
        
        self.agent_order: list[str] = list(self.providers.keys())
        
        # Cache individualizado para cada provedor (para estatísticas)
        self.caches: Dict[str, ResponseCache] = defaultdict(
            lambda: ResponseCache(
                max_size=getattr(config, 'max_cache_size', 100),
                ttl_seconds=getattr(config, 'cache_ttl', 180)
            )
        )
        
        # Modelos para exibição
        self.models: dict[str, str] = {}
        for nome, p in self.providers.items():
            if hasattr(p, 'get_modelo_atual'):
                self.models[nome] = p.get_modelo_atual()
            elif hasattr(p, 'get_modelo'):
                self.models[nome] = p.get_modelo()
            else:
                self.models[nome] = "desconhecido"
        
        self.state = DebateState()
        self._initialized = True
        
        if self.agent_order:
            logger.info(f"Agentes: {', '.join(self.agent_order)}")
        else:
            logger.error("Nenhum agente disponível!")
    
    def __enter__(self):
        logger.info("📂 Entrando no contexto do orquestrador")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
    
    def shutdown(self) -> None:
        logger.info("🔄 Liberando recursos do orquestrador...")
        try:
            for cache in self.caches.values():
                cache.clear()
            logger.info("✅ Caches liberados")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao liberar caches: {e}")
        
        for nome, provider in self.providers.items():
            try:
                if hasattr(provider, 'close'):
                    provider.close()
                logger.info(f"✅ Provedor {nome} fechado")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao fechar {nome}: {e}")
        
        self._initialized = False
        logger.info("✅ Orquestrador finalizado")
    
    def _executar_com_fallback(self, nome: str, prompt: str, papel: str, max_tokens: int, temperature: float) -> str:
        """Executa um provider, e se falhar, tenta o fallback configurado."""
        provider = self.providers.get(nome)
        if not provider:
            return f"[Erro: provedor {nome} não encontrado]"
        
        try:
            if hasattr(provider, 'call'):
                resposta = provider.call(prompt, papel=papel, max_tokens=max_tokens, temperature=temperature)
            elif hasattr(provider, 'gerar_resposta'):
                resposta = provider.gerar_resposta(prompt, usar_cache=False)
            else:
                resposta = "[Erro: provedor sem método de geração]"
            
            if not resposta.startswith("[Erro") and not resposta.startswith("[Circuit"):
                return resposta
            
            logger.warning(f"⚠️ {nome} retornou erro: {resposta[:80]}...")
            
        except Exception as e:
            resposta = f"[Erro inesperado em {nome}: {str(e)[:100]}]"
            logger.error(f"❌ {nome} falhou: {str(e)[:80]}")
        
        # Verificar fallback
        fallback_provider = self.config.fallback_map.get(nome)
        if fallback_provider and fallback_provider in self.providers:
            logger.info(f"🔄 Usando {fallback_provider} como fallback para {nome}...")
            return self._executar_com_fallback(
                fallback_provider, prompt, papel, max_tokens, temperature
            )
        
        return resposta
    
    def run_round(self, tema: str, rodada: int) -> dict[str, str]:
        if not self._initialized:
            raise ProviderError("Orquestrador não inicializado")
        
        if not self.agent_order:
            return {"Erro": "Nenhum agente disponível"}
        
        if rodada > 1:
            try:
                for cache in self.caches.values():
                    cache.clear()
                logger.info("🧹 Caches limpos para nova rodada")
            except Exception as e:
                raise CacheError(f"Erro ao limpar caches: {e}")
        
        respostas: dict[str, str] = {}
        ordem: list[str] = self.agent_order.copy()
        random.shuffle(ordem)
        
        for nome in ordem:
            provider = self.providers.get(nome)
            if not provider:
                continue
            
            logger.info(f"💭 {nome} pensando...")
            
            prompt = self._criar_prompt(tema)
            
            if hasattr(provider, '_especialidades'):
                papel = ""
            else:
                papel = prompt_builder.get_papel(nome)
            
            max_tokens = self.config.max_tokens_por_agente.get(nome, 800)
            if 'ollama' in nome:
                max_tokens = self.config.max_tokens_por_agente.get('ollama', 400)
            
            resposta = self._executar_com_fallback(nome, prompt, papel, max_tokens, 0.3)
            
            self.state.add_fala(nome, resposta)
            respostas[nome] = resposta
            time.sleep(0.2)
        
        self.state.clear_rodada()
        return respostas
    
    def continuar_chat(self, mensagem: str, incluir_historico: bool = True) -> dict[str, str]:
        if not self._initialized:
            raise ProviderError("Orquestrador não inicializado")
        
        respostas: dict[str, str] = {}
        
        contexto = ""
        if incluir_historico and self.state.todas_falas:
            ultimas = self.state.todas_falas[-5:]
            contexto = "## CONTEXTO DO DEBATE ANTERIOR:\n"
            for nome, texto in ultimas:
                contexto += f"[{nome}]: {texto[:200]}\n"
            contexto += "\n"
        
        prompt = f"{contexto}## PERGUNTA DO USUÁRIO:\n{mensagem}\n\n## SUA RESPOSTA (seja direto, continue a linha de raciocínio se for o caso):"
        
        for nome in self.agent_order:
            provider = self.providers.get(nome)
            if not provider:
                continue
            
            logger.info(f"💭 {nome} pensando...")
            
            if hasattr(provider, '_especialidades'):
                papel = ""
            else:
                papel = prompt_builder.get_papel(nome)
            
            max_tokens = self.config.max_tokens_por_agente.get(nome, 800)
            if 'ollama' in nome:
                max_tokens = self.config.max_tokens_por_agente.get('ollama', 400)
            
            resposta = self._executar_com_fallback(nome, prompt, papel, max_tokens, 0.3)
            
            self.state.add_fala(nome, resposta)
            respostas[nome] = resposta
            time.sleep(0.2)
        
        return respostas
    
    def _criar_prompt(self, tema: str) -> str:
        tema_limitado: str = tema[:3500] if len(tema) > 3500 else tema
        return f"""## TEMA PARA ANÁLISE:

{tema_limitado}

## SUA ANÁLISE (seja direto, sem saudações):"""
    
    def get_debate_summary(self) -> str:
        if not self.state.historico:
            return "Nenhum histórico disponível."
        historico: str = self.state.historico
        return historico[-500:] if len(historico) > 500 else historico
    
    def get_metrics(self) -> dict:
        return {
            'agentes': self.agent_order,
            'models': {nome: self.models.get(nome) for nome in self.agent_order},
            'total_respostas': len(self.state.todas_falas),
            'provedores_ativos': len(self.providers),
            'initialized': self._initialized
        }