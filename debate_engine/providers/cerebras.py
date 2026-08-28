#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import List
from .base import BaseProvider


class CerebrasProvider(BaseProvider):
    """Provedor para API Cerebras com retry e fallback de modelo."""

    def __init__(self, api_key: str, modelos: List[str] = None, rate_limit: int = 8):
        super().__init__(nome="cerebras", modelos=modelos or ["llama-3.3-70b"], rate_limit=rate_limit)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url="https://api.cerebras.ai/v1")

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
                timeout=30
            )
            return response.choices[0].message.content if response.choices else ""

        for modelo in self._modelos:
            self._modelo_atual = modelo
            for tentativa in range(3):
                try:
                    resultado = self._executar_com_resiliencia(prompt, _chamada, usar_cache=False)
                    if not resultado.startswith("[Erro") and not resultado.startswith("[Circuit"):
                        return resultado
                    if "429" in resultado or "503" in resultado:
                        espera = 5 * (tentativa + 1)
                        print(f"⏳ Cerebras: {resultado[:40]}, aguardando {espera}s (tentativa {tentativa+1}/3)...")
                        time.sleep(espera)
                        continue
                    else:
                        return resultado
                except Exception as e:
                    print(f"⚠️ Cerebras: erro inesperado: {str(e)[:60]}")
                    if tentativa < 2:
                        time.sleep(5)
                    continue
            print(f"⚠️ Cerebras ({modelo}): falhou após 3 tentativas, tentando próximo modelo...")

        return "[Erro Cerebras: Todos os modelos falharam]"

    def get_nome(self) -> str:
        return self._nome

    def get_modelo_atual(self) -> str:
        return self._modelo_atual

    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos