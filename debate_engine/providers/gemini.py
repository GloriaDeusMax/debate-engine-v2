#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import time
from typing import List
from google import genai
from google.genai import types
from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Provedor para API Gemini (Google) com retry e fallback de modelo."""

    def __init__(self, api_key: str, modelos: List[str] = None, rate_limit: int = 5):
        super().__init__(nome="gemini", modelos=modelos or [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-2.5-flash"
        ], rate_limit=rate_limit)
        self.client = genai.Client(api_key=api_key)

    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        prompt_completo = f"{papel}\n\n{prompt}"

        def _chamada() -> str:
            chat = self.client.chats.create(
                model=self._modelo_atual,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            )
            response = chat.send_message(prompt_completo[:2500])
            return response.text if response.text else ""

        # Tenta cada modelo da lista, com retry exponencial para erros 429/503
        for modelo in self._modelos:
            self._modelo_atual = modelo
            for tentativa in range(3):  # até 3 tentativas por modelo
                try:
                    resultado = self._executar_com_resiliencia(prompt, _chamada, usar_cache=False)
                    if not resultado.startswith("[Erro") and not resultado.startswith("[Circuit"):
                        return resultado
                    # Se erro transitório, tenta de novo com backoff progressivo
                    if "429" in resultado or "503" in resultado:
                        espera = 5 * (tentativa + 1)  # 5s, 10s, 15s
                        print(f"⏳ Gemini: {resultado[:40]}, aguardando {espera}s (tentativa {tentativa+1}/3)...")
                        time.sleep(espera)
                        continue
                    else:
                        # Erro permanente – não adianta tentar de novo
                        return resultado
                except Exception as e:
                    print(f"⚠️ Gemini: erro inesperado: {str(e)[:60]}")
                    if tentativa < 2:
                        time.sleep(5)
                    continue
            # Se todos os retries falharam para este modelo, tenta o próximo
            print(f"⚠️ Gemini ({modelo}): falhou após 3 tentativas, tentando próximo modelo...")

        return "[Erro Gemini: Todos os modelos falharam]"

    def get_nome(self) -> str:
        return self._nome

    def get_modelo_atual(self) -> str:
        return self._modelo_atual

    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos