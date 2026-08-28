#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict
from ..config import config
from .gemini import GeminiProvider
from .groq import GroqProvider
from .openrouter import OpenRouterProvider
from .nvidia import NvidiaProvider
from .ollama import OllamaProvider
from .mistral import MistralProvider
from .base import BaseProvider

# Modelos Ollama prioritários (primeiro é o principal, demais são fallback)
OLLAMA_MODELOS_PRIORITARIOS = [
    "llama3.2:latest",
    "mistral:latest",
    "qwen2.5:latest",
    "phi3:latest"
]


def criar_provedores() -> Dict[str, BaseProvider]:
    """Factory que cria provedores usando as configurações do config (Pydantic)."""
    providers: Dict[str, BaseProvider] = {}

    if config.gemini_api_key:
        providers["gemini"] = GeminiProvider(
            config.gemini_api_key,
            modelos=config.gemini_modelos,
            rate_limit=config.rate_limit_gemini,
        )

    if config.groq_api_key:
        providers["groq"] = GroqProvider(
            config.groq_api_key,
            modelos=config.groq_modelos,
            rate_limit=config.rate_limit_groq,
        )

    if config.openrouter_api_key:
        providers["openrouter"] = OpenRouterProvider(
            config.openrouter_api_key,
            modelos=config.openrouter_modelos,
            rate_limit=config.rate_limit_openrouter,
        )

    if config.nvidia_api_key:
        providers["nvidia"] = NvidiaProvider(
            config.nvidia_api_key,
            rate_limit=config.rate_limit_nvidia,
        )

    if config.mistral_api_key:
        providers["mistral"] = MistralProvider(
            config.mistral_api_key,
            modelos=config.mistral_modelos,
            rate_limit=config.rate_limit_mistral,
        )

    # Ollama - detecta via API local (não precisa de chave)
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            modelos_instalados = [m["name"] for m in r.json().get("models", [])]
            for modelo in OLLAMA_MODELOS_PRIORITARIOS:
                if modelo in modelos_instalados:
                    nome_agente = "ollama_" + modelo.replace(":", "_").replace(".", "_")
                    providers[nome_agente] = OllamaProvider(
                        nome=nome_agente,
                        modelo=modelo,
                        modelos_fallback=[
                            m for m in OLLAMA_MODELOS_PRIORITARIOS
                            if m in modelos_instalados and m != modelo
                        ]
                    )
                    break
    except Exception:
        pass

    return providers