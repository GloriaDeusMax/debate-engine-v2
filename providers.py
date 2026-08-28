#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
providers.py - Provedores de LLM
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from collections import deque

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    from google import genai
except ImportError as e:
    logger.error(f"Erro ao importar: {e}")
    exit(1)


class RateLimiter:
    def __init__(self, max_calls_per_minute=10):
        self.max_calls = max_calls_per_minute
        self.calls = deque()
    
    def wait(self):
        now = time.time()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        
        if len(self.calls) >= self.max_calls:
            sleep_time = 60 - (now - self.calls[0]) + 1
            logger.info(f"Rate limit: aguardando {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.calls.append(time.time())


class LLMProvider(ABC):
    @abstractmethod
    def gerar_resposta(self, prompt, max_tokens=400):
        pass
    
    @abstractmethod
    def get_nome(self):
        pass
    
    @abstractmethod
    def get_modelo(self):
        pass


class GeminiProvider(LLMProvider):
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self._nome = "gemini"
        self.modelos = [
            'gemini-3.7-flash',
            'gemini-3.6-flash',
            'gemini-3.5-flash',
            'gemini-2.5-flash',
            'gemini-2.5-pro',
        ]
        self._modelo_atual = self.modelos[0]
        self.rate_limiter = RateLimiter(max_calls_per_minute=10)
        self.ultimo_erro = None
        logger.info("Gemini provider criado")
    
    def gerar_resposta(self, prompt, max_tokens=400):
        self.rate_limiter.wait()
        
        for modelo in self.modelos:
            try:
                logger.info(f"Tentando Gemini: {modelo}")
                chat = self.client.chats.create(model=modelo)
                response = chat.send_message(prompt)
                
                if response.text and len(response.text) > 50:
                    self._modelo_atual = modelo
                    logger.info(f"Gemini funcionou com: {modelo}")
                    return response.text[:800]
                    
            except Exception as e:
                erro_msg = str(e)
                self.ultimo_erro = erro_msg
                logger.warning(f"Gemini {modelo}: {erro_msg[:60]}")
                
                if "429" in erro_msg:
                    logger.info("Rate limit, aguardando 15s")
                    time.sleep(15)
                continue
        
        return f"[Erro Gemini: {self.ultimo_erro[:100]}]"
    
    def get_nome(self):
        return self._nome
    
    def get_modelo(self):
        return self._modelo_atual


class GroqProvider(LLMProvider):
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self._nome = "groq"
        self.modelos = [
            'openai/gpt-oss-120b',
            'openai/gpt-oss-20b',
            'groq/compound',
            'groq/compound-mini',
        ]
        self._modelo_atual = self.modelos[0]
        self.rate_limiter = RateLimiter(max_calls_per_minute=15)
        self.ultimo_erro = None
        logger.info("Groq provider criado")
    
    def gerar_resposta(self, prompt, max_tokens=400):
        self.rate_limiter.wait()
        
        for modelo in self.modelos:
            try:
                logger.info(f"Tentando Groq: {modelo}")
                
                response = self.client.chat.completions.create(
                    model=modelo,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
                content = response.choices[0].message.content
                
                if content and len(content) > 20:
                    self._modelo_atual = modelo
                    logger.info(f"Groq funcionou com: {modelo}")
                    return content[:800]
                    
            except Exception as e:
                erro_msg = str(e)
                self.ultimo_erro = erro_msg
                logger.warning(f"Groq {modelo}: {erro_msg[:60]}")
                
                if "429" in erro_msg:
                    logger.info("Rate limit, aguardando 15s")
                    time.sleep(15)
                continue
        
        return f"[Erro Groq: {self.ultimo_erro[:100]}]"
    
    def get_nome(self):
        return self._nome
    
    def get_modelo(self):
        return self._modelo_atual


def criar_provedores():
    providers = {}
    
    gemini_key = os.environ.get('GEMINI_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')
    
    if gemini_key:
        try:
            providers['gemini'] = GeminiProvider(gemini_key)
        except Exception as e:
            logger.error(f"Erro ao criar Gemini: {e}")
    
    if groq_key:
        try:
            providers['groq'] = GroqProvider(groq_key)
        except Exception as e:
            logger.error(f"Erro ao criar Groq: {e}")
    
    return providers


if __name__ == "__main__":
    providers = criar_provedores()
    for nome, provider in providers.items():
        print(f"{nome}: {provider.get_modelo()}")