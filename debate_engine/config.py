#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
config.py - Configurações centralizadas com validação via Pydantic.

Este módulo carrega variáveis de ambiente do .env (se existir) e valida
os tipos e valores usando Pydantic BaseSettings. Suporta 8 provedores
de LLM: Gemini, Groq, OpenRouter, NVIDIA, Ollama, Mistral, Cerebras e
OpenAI (opcional).
"""

import json
from pathlib import Path
from typing import Dict, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Diretório raiz do projeto (subindo 2 níveis: debate_engine/config.py -> projeto/)
PROJECT_DIR = Path(__file__).resolve().parent.parent


class Config(BaseSettings):
    # ===== PROVEDORES (chaves de API) =====
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    nvidia_api_key: str = ""
    mistral_api_key: str = ""
    cerebras_api_key: str = ""

    # ===== MODELOS =====
    # Gemini
    gemini_modelos: List[str] = ["gemini-3.6-flash", "gemini-3.5-flash"]
    # Groq
    groq_modelos: List[str] = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    # OpenRouter
    openrouter_modelos: List[str] = ["openrouter/auto", "meta-llama/llama-3.3-70b-instruct:free"]
    # NVIDIA
    nvidia_modelos: List[str] = ["nvidia/nemotron-3-ultra-550b-a55b"]
    # Mistral
    mistral_modelos: List[str] = ["mistral-small-latest", "mistral-medium-latest"]
    # Cerebras (modelos disponíveis na conta)
    cerebras_modelos: List[str] = [
        "gemma-4-31b",
        "gpt-oss-120b",
    ]

    # ===== PARÂMETROS GERAIS =====
    temperature: float = 0.3
    rate_limit_gemini: int = 5
    rate_limit_groq: int = 8
    rate_limit_openrouter: int = 5
    rate_limit_nvidia: int = 8
    rate_limit_mistral: int = 5
    rate_limit_cerebras: int = 8

    # ===== OLLAMA (local) =====
    ollama_url: str = "http://localhost:11434/api/generate"
    timeout_ollama: int = 150
    ollama_num_ctx: int = 8192
    ollama_modelos_preferidos: List[str] = [
        "llama3.2", "llama3.1", "llama3", "qwen2.5",
        "qwen", "gemma2", "gemma", "mistral", "phi"
    ]

    # ===== LIMITES DE TOKENS POR AGENTE =====
    max_tokens_por_agente: Dict[str, int] = {
        'gemini': 800,
        'groq': 1000,
        'openrouter': 800,
        'nvidia': 800,
        'mistral': 800,
        'cerebras': 800,
        'ollama': 400,
    }

    # ===== RODADAS =====
    max_rounds_padrao: int = 2

    # ===== RETRY / BACKOFF =====
    max_tentativas: int = 2
    timeout_entre_tentativas: int = 3
    backoff_base: int = 3

    # ===== LOGS E CACHE =====
    logs_dir: str = str(PROJECT_DIR / "logs")
    log_level: str = "INFO"
    cache_dir: str = str(PROJECT_DIR / "cache")
    max_cache_size: int = 100
    cache_ttl: int = 180

    # ===== FALLBACK DE PROVEDOR (via .env) =====
    fallback_map: Dict[str, str] = {}

    @field_validator("fallback_map", mode="before")
    @classmethod
    def parse_fallback_map(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v

    # ===== CONFIGURAÇÃO DO PYDANTIC =====
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


config = Config()