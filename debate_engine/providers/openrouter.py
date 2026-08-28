#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import List
from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """Provedor para API OpenRouter com retry e fallback de modelo."""

    def __init__(self, api_key: str, modelos: List[str] = None, rate_limit: int = 5):
        super().__init__(nome="openrouter", modelos=modelos or [
            "openrouter/auto",
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen3-235b-a22b:free",
            "z-ai/glm-4.5-air:free",
            "deepseek/deepseek-chat:free"
        ], rate_limit=rate_limit)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        prompt_completo = f"{papel}\n\n{prompt}"

        def _chamada() -> str:
            response = self.client.chat.completions.create(
                model=self._modelo_atual,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers={
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "4KINGS Debate"
                }
            )
            return response.choices[0].message.content if response.choices else ""

        for modelo in self._modelos:
            self._modelo_atual = modelo
            for tentativa in range(2):  # menos tentativas para não demorar
                try:
                    resultado = self._executar_com_resiliencia(prompt, _chamada, usar_cache=False)
                    if not resultado.startswith("[Erro") and not resultado.startswith("[Circuit"):
                        return resultado
                    if "429" in resultado or "503" in resultado:
                        espera = 4 * (tentativa + 1)
                        print(f"⏳ OpenRouter: {resultado[:40]}, aguardando {espera}s (tentativa {tentativa+1}/2)...")
                        time.sleep(espera)
                        continue
                    else:
                        return resultado
                except Exception as e:
                    print(f"⚠️ OpenRouter: erro inesperado: {str(e)[:60]}")
                    if tentativa < 1:
                        time.sleep(4)
                    continue
            print(f"⚠️ OpenRouter ({modelo}): falhou após 2 tentativas, tentando próximo modelo...")

        return "[Erro OpenRouter: Todos os modelos falharam]"

    def get_nome(self) -> str:
        return self._nome

    def get_modelo_atual(self) -> str:
        return self._modelo_atual

    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos