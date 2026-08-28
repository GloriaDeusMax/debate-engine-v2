#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import requests
from typing import List
from ..config import config
from .base import BaseProvider


class OllamaProvider(BaseProvider):
    """Provedor local via Ollama com fallback para múltiplos modelos locais."""

    def __init__(self, nome: str, modelo: str, modelos_fallback: List[str] = None, rate_limit: int = 999, url: str = None):
        super().__init__(nome=nome, modelos=[modelo] + (modelos_fallback or []), rate_limit=rate_limit)
        self.url = url or getattr(config, 'ollama_url', "http://localhost:11434/api/generate")
        self._modelo_atual = modelo

    def call(self, prompt: str, papel: str = "", max_tokens: int = 400, temperature: float = 0.3) -> str:
        prompt_completo = f"{papel}\n\n{prompt}" if papel else prompt

        def _chamada() -> str:
            num_ctx = getattr(config, 'ollama_num_ctx', 8192)
            payload = {
                "model": self._modelo_atual,
                "prompt": prompt_completo,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "num_ctx": num_ctx
                }
            }
            timeout = getattr(config, 'timeout_ollama', 150)
            response = requests.post(self.url, json=payload, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                raise Exception(f"HTTP {response.status_code}")

        for modelo in self._modelos:
            self._modelo_atual = modelo
            try:
                resultado = self._executar_com_resiliencia(prompt, _chamada, usar_cache=False)
                if not resultado.startswith("[Erro") and not resultado.startswith("[Circuit"):
                    return resultado
            except Exception as e:
                print(f"⚠️ Ollama ({modelo}): {str(e)[:60]}, tentando próximo...")
                continue

        return f"[Erro {self._nome}: Todos os modelos locais falharam]"

    def get_nome(self) -> str:
        return self._nome

    def get_modelo_atual(self) -> str:
        return self._modelo_atual

    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos