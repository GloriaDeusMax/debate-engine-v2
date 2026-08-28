#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
providers.py - Provedores de LLM com Circuit Breaker, Cache e Rate Limiting
Versão com segurança aprimorada - NUNCA expõe chaves de API
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

from .config import config
from .circuit_breaker import gemini_cb, groq_cb
from .cache import gemini_cache, groq_cache
from .prompt_builder import prompt_builder
from .token_manager import token_manager
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    from google import genai
except ImportError as e:
    logger.error(f"Erro ao importar dependências: {e}")
    exit(1)


class LLMProvider(ABC):
    """Interface base para provedores de LLM"""
    
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


class GeminiProvider(LLMProvider):
    """Provedor para API Gemini com segurança aprimorada"""
    
    def __init__(self, api_key: str):
        # NUNCA logar a chave completa
        self._api_key = api_key
        self._api_key_masked = self._mask_key(api_key)
        
        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Erro ao inicializar Gemini client: {e}")
            raise
        
        self._nome = "gemini"
        self.modelos = config.gemini_modelos
        self._modelo_atual = self.modelos[0]
        self.rate_limiter = RateLimiter(max_calls_per_minute=config.rate_limit_gemini)
        self.cb = gemini_cb
        self.cache = gemini_cache
        self.ultimo_erro: Optional[str] = None
        
        # Papel fixo (sem saudações)
        self.papel_fixo = prompt_builder.get_papel('gemini')
        
        # Log seguro (NUNCA mostra a chave)
        logger.info(f"Gemini provider criado com sucesso (chave: {self._api_key_masked})")
    
    def _mask_key(self, key: str) -> str:
        """Mascara a chave para logs seguros."""
        if not key:
            return "[NÃO CONFIGURADA]"
        if len(key) <= 8:
            return "[CHAVE CURTA]"
        return f"{key[:4]}...{key[-4:]}"
    
    def gerar_resposta(self, prompt: str, max_tokens: int = 400, usar_cache: bool = True) -> str:
        """
        Gera resposta com Circuit Breaker, Cache e Rate Limiting.
        
        Args:
            prompt: O prompt para enviar ao modelo
            max_tokens: Número máximo de tokens na resposta
            usar_cache: Se True, usa cache; Se False, ignora cache (para debates)
        """
        
        # 1. Verificar cache primeiro (apenas se permitido)
        if usar_cache:
            cached = self.cache.get(prompt, self._modelo_atual, max_tokens, config.temperature)
            if cached:
                logger.info(f"Gemini: resposta do cache")
                return cached
        else:
            logger.info(f"Gemini: cache ignorado (usar_cache=False)")
        
        # 2. Verificar Circuit Breaker
        if not self.cb.can_execute():
            logger.warning(f"Gemini: Circuit Breaker OPEN - pulando chamada")
            return "[Circuit Breaker: Gemini temporariamente indisponível]"
        
        # 3. Rate Limiting
        self.rate_limiter.wait()
        
        # 4. Construir prompt completo
        prompt_completo = f"{self.papel_fixo}\n\n{prompt}"
        
        # 5. Verificar tokens
        if not token_manager.can_afford(prompt_completo):
            prompt_completo = token_manager.truncate_to_tokens(prompt_completo, 2000)
        
        # 6. Tentar cada modelo com fallback
        for modelo in self.modelos:
            try:
                logger.info(f"Tentando Gemini: {modelo}")
                
                response = self.client.models.generate_content(
                    model=modelo,
                    contents=prompt_completo[:2500]
                )
                
                if response.text and len(response.text) > 50:
                    self._modelo_atual = modelo
                    self.cb.record_success()
                    token_manager.consume_tokens(response.text)
                    
                    # Salvar no cache (apenas se usar_cache=True)
                    if usar_cache:
                        self.cache.set(prompt, self._modelo_atual, max_tokens, config.temperature, response.text)
                    
                    logger.info(f"✅ Gemini funcionou com: {modelo}")
                    return response.text[:800]
                    
            except Exception as e:
                erro_msg = str(e)
                self.ultimo_erro = erro_msg
                self.cb.record_failure(erro_msg)
                
                # Tratar erros específicos sem expor informações sensíveis
                if "503" in erro_msg or "UNAVAILABLE" in erro_msg:
                    logger.warning(f"Gemini {modelo}: serviço indisponível")
                    continue
                elif "429" in erro_msg or "RESOURCE_EXHAUSTED" in erro_msg:
                    logger.warning(f"Gemini {modelo}: rate limit, aguardando...")
                    time.sleep(5)
                    continue
                elif "404" in erro_msg or "not found" in erro_msg.lower():
                    logger.warning(f"Gemini {modelo}: modelo não encontrado")
                    continue
                else:
                    # Log seguro - não expõe detalhes da API
                    logger.warning(f"Gemini {modelo}: erro na chamada")
                    continue
        
        # Se todos os modelos falharam
        return f"[Erro Gemini: {self.ultimo_erro[:100] if self.ultimo_erro else 'erro desconhecido'}]"
    
    def get_nome(self) -> str:
        return self._nome
    
    def get_modelo(self) -> str:
        return self._modelo_atual


class GroqProvider(LLMProvider):
    """Provedor para API Groq com segurança aprimorada"""
    
    def __init__(self, api_key: str):
        # NUNCA logar a chave completa
        self._api_key = api_key
        self._api_key_masked = self._mask_key(api_key)
        
        try:
            self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        except Exception as e:
            logger.error(f"Erro ao inicializar Groq client: {e}")
            raise
        
        self._nome = "groq"
        self.modelos = config.groq_modelos
        self._modelo_atual = self.modelos[0]
        self.rate_limiter = RateLimiter(max_calls_per_minute=config.rate_limit_groq)
        self.cb = groq_cb
        self.cache = groq_cache
        self.ultimo_erro: Optional[str] = None
        
        # Papel fixo (sem saudações)
        self.papel_fixo = prompt_builder.get_papel('groq')
        
        # Log seguro (NUNCA mostra a chave)
        logger.info(f"Groq provider criado com sucesso (chave: {self._api_key_masked})")
    
    def _mask_key(self, key: str) -> str:
        """Mascara a chave para logs seguros."""
        if not key:
            return "[NÃO CONFIGURADA]"
        if len(key) <= 8:
            return "[CHAVE CURTA]"
        return f"{key[:4]}...{key[-4:]}"
    
    def gerar_resposta(self, prompt: str, max_tokens: int = 400, usar_cache: bool = True) -> str:
        """
        Gera resposta com Circuit Breaker, Cache e Rate Limiting.
        
        Args:
            prompt: O prompt para enviar ao modelo
            max_tokens: Número máximo de tokens na resposta
            usar_cache: Se True, usa cache; Se False, ignora cache (para debates)
        """
        
        # 1. Verificar cache primeiro (apenas se permitido)
        if usar_cache:
            cached = self.cache.get(prompt, self._modelo_atual, max_tokens, config.temperature)
            if cached:
                logger.info(f"Groq: resposta do cache")
                return cached
        else:
            logger.info(f"Groq: cache ignorado (usar_cache=False)")
        
        # 2. Verificar Circuit Breaker
        if not self.cb.can_execute():
            logger.warning(f"Groq: Circuit Breaker OPEN - pulando chamada")
            return "[Circuit Breaker: Groq temporariamente indisponível]"
        
        # 3. Rate Limiting
        self.rate_limiter.wait()
        
        # 4. Construir prompt completo
        prompt_completo = f"{self.papel_fixo}\n\n{prompt}"
        
        # 5. Verificar tokens
        if not token_manager.can_afford(prompt_completo):
            prompt_completo = token_manager.truncate_to_tokens(prompt_completo, 2000)
        
        # 6. Tentar cada modelo com fallback
        for modelo in self.modelos:
            try:
                logger.info(f"Tentando Groq: {modelo}")
                
                response = self.client.chat.completions.create(
                    model=modelo,
                    messages=[{"role": "user", "content": prompt_completo[:3000]}],
                    max_tokens=max_tokens,
                    temperature=config.temperature
                )
                content = response.choices[0].message.content
                
                if content and len(content) > 20:
                    self._modelo_atual = modelo
                    self.cb.record_success()
                    token_manager.consume_tokens(content)
                    
                    # Salvar no cache (apenas se usar_cache=True)
                    if usar_cache:
                        self.cache.set(prompt, self._modelo_atual, max_tokens, config.temperature, content)
                    
                    logger.info(f"✅ Groq funcionou com: {modelo}")
                    return content[:800]
                    
            except Exception as e:
                erro_msg = str(e)
                self.ultimo_erro = erro_msg
                self.cb.record_failure(erro_msg)
                
                # Tratar erros específicos sem expor informações sensíveis
                if "429" in erro_msg or "rate limit" in erro_msg.lower():
                    logger.warning(f"Groq {modelo}: rate limit, aguardando...")
                    time.sleep(5)
                    continue
                elif "404" in erro_msg or "not found" in erro_msg.lower():
                    logger.warning(f"Groq {modelo}: modelo não encontrado")
                    continue
                else:
                    # Log seguro - não expõe detalhes da API
                    logger.warning(f"Groq {modelo}: erro na chamada")
                    continue
        
        # Se todos os modelos falharam
        return f"[Erro Groq: {self.ultimo_erro[:100] if self.ultimo_erro else 'erro desconhecido'}]"
    
    def get_nome(self) -> str:
        return self._nome
    
    def get_modelo(self) -> str:
        return self._modelo_atual


def criar_provedores() -> Dict[str, LLMProvider]:
    """
    Factory para criar todos os provedores disponíveis.
    ⚠️ NUNCA loga chaves de API.
    """
    providers = {}
    
    # Verificar Gemini sem expor a chave
    if config.has_gemini():
        try:
            providers['gemini'] = GeminiProvider(config.gemini_api_key)
            logger.info("✅ Gemini configurado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar Gemini: {e}")
    else:
        logger.info("ℹ️ Gemini: chave não configurada (opcional)")
    
    # Verificar Groq sem expor a chave
    if config.has_groq():
        try:
            providers['groq'] = GroqProvider(config.groq_api_key)
            logger.info("✅ Groq configurado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar Groq: {e}")
    else:
        logger.info("ℹ️ Groq: chave não configurada (opcional)")
    
    if not providers:
        logger.warning("⚠️ Nenhum provedor configurado!")
    
    return providers


if __name__ == "__main__":
    # Teste rápido (NUNCA expõe chaves)
    print("🧪 Testando provedores...")
    providers = criar_provedores()
    for nome, provider in providers.items():
        print(f"📌 {nome}: {provider.get_modelo()}")