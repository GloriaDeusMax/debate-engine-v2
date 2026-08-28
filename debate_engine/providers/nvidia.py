#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List, Dict
from .base import BaseProvider


class NvidiaProvider(BaseProvider):
    """Provedor para API NVIDIA NIM (apenas modelos gratuitos funcionais)."""

    def __init__(self, api_key: str, modelos: List[Dict] = None, rate_limit: int = 30):
        if not modelos:
            modelos = [
                {"modelo": "nvidia/nemotron-3-nano-30b-a3b", "especialidade": "Especialista em Respostas Rápidas e Diretas"},
                {"modelo": "nvidia/nemotron-3-super-120b-a12b", "especialidade": "Especialista em Análise Profunda de Sistemas"},
            ]

        self._modelos = [item["modelo"] for item in modelos]
        self._especialidades = {item["modelo"]: item["especialidade"] for item in modelos}

        super().__init__(nome="nvidia", modelos=self._modelos, rate_limit=rate_limit)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")

    def call(self, prompt: str, papel: str = "", max_tokens: int = 800, temperature: float = 0.3) -> str:
        if not papel:
            papel = self._especialidades.get(self._modelo_atual, "Assistente especializado.")

        prompt_completo = f"{papel}\n\n{prompt}"

        def _chamada() -> str:
            response = self.client.chat.completions.create(
                model=self._modelo_atual,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content if response.choices else ""

        for modelo in self._modelos:
            self._modelo_atual = modelo
            papel_atual = self._especialidades.get(modelo, papel)

            try:
                resultado = self._executar_com_resiliencia(prompt, _chamada, usar_cache=False)
            except Exception as e:
                resultado = f"[Erro: {str(e)[:100]}]"

            # Se 404/410 -> modelo não acessível, pula sem retry
            if any(x in resultado.lower() for x in ["404", "410", "not found", "model not found"]):
                print(f"⚠️ Nvidia ({modelo}): modelo não acessível, pulando...")
                continue

            if not resultado.startswith("[Erro") and not resultado.startswith("[Circuit"):
                return resultado

        return f"[Erro {self._nome}: Todos os modelos falharam ou descontinuados]"

    def get_nome(self) -> str:
        return "nvidia"

    def get_modelo_atual(self) -> str:
        return self._modelo_atual

    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos