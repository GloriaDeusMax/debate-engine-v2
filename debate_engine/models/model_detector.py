#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import List
from openai import OpenAI
from google import genai


class ModelStrategy(ABC):
    @abstractmethod
    def detectar(self, api_key: str) -> List[str]:
        pass


class GeminiModelStrategy(ModelStrategy):
    def detectar(self, api_key: str) -> List[str]:
        try:
            client = genai.Client(api_key=api_key)
            modelos = client.models.list()
            nomes = []
            for m in modelos:
                if hasattr(m, 'name'):
                    nome = m.name
                    if 'gemini' in nome.lower():
                        if nome.startswith('models/'):
                            nome = nome[7:]
                        nomes.append(nome)
            prioridades = ['gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
            resultado = []
            for p in prioridades:
                if p in nomes and p not in resultado:
                    resultado.append(p)
            for m in nomes:
                if m not in resultado:
                    resultado.append(m)
            return resultado
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelos Gemini: {e}")
            return ['gemini-3.6-flash', 'gemini-3.5-flash']


class GroqModelStrategy(ModelStrategy):
    def detectar(self, api_key: str) -> List[str]:
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            modelos = client.models.list()
            disponiveis = [m.id for m in modelos.data]
            chat_models = [m for m in disponiveis if not any(x in m.lower() for x in ['whisper', 'embed', 'guard', 'tts'])]
            prioridades = ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'groq/compound']
            resultado = []
            for p in prioridades:
                if p in chat_models and p not in resultado:
                    resultado.append(p)
            for m in chat_models:
                if m not in resultado:
                    resultado.append(m)
            return resultado
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelos Groq: {e}")
            return ['openai/gpt-oss-120b', 'openai/gpt-oss-20b']


class OpenRouterModelStrategy(ModelStrategy):
    def detectar(self, api_key: str) -> List[str]:
        try:
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            modelos_gratuitos = ['openrouter/free', 'nvidia/nemotron-3-nano-30b-a3b:free']
            try:
                modelos = client.models.list()
                modelos_api = [m.id for m in modelos.data]
                disponiveis = []
                for modelo in modelos_gratuitos:
                    if modelo in modelos_api:
                        disponiveis.append(modelo)
                if disponiveis:
                    return disponiveis
            except:
                pass
            return modelos_gratuitos
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelos OpenRouter: {e}")
            return ['openrouter/free', 'nvidia/nemotron-3-nano-30b-a3b:free']


class ModelDetector:
    def __init__(self, provider: str):
        self.provider = provider
        self.strategy = self._get_strategy()
    
    def _get_strategy(self) -> ModelStrategy:
        if self.provider == 'gemini':
            return GeminiModelStrategy()
        elif self.provider == 'groq':
            return GroqModelStrategy()
        elif self.provider == 'openrouter':
            return OpenRouterModelStrategy()
        else:
            raise ValueError(f"Provedor {self.provider} não suportado")
    
    def detectar(self, api_key: str) -> List[str]:
        return self.strategy.detectar(api_key)