#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List
from openai import OpenAI

from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """Provedor OpenRouter com Strategy Pattern"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self._nome = "openrouter"
        self.client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        
        self._modelos = ['openrouter/free', 'nvidia/nemotron-3-nano-30b-a3b:free']
        self._modelo_atual = self._modelos[0]
        
        self._papel_fixo = """Você é um sintetizador e planejador estratégico.

REGRAS:
- NUNCA se apresente ou se cumprimente
- Una os argumentos dos outros agentes
- Aponte convergências e divergências
- Sugira o próximo passo do debate
- Responda em Português do Brasil

FORMATO:
## Síntese
- Convergências
- Divergências
- Próximo passo"""
        
        print(f"✅ OpenRouter configurado - modelos: {', '.join(self._modelos[:3])}...")
    
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Executa chamada ao OpenRouter"""
        
        def _chamada():
            prompt_completo = f"{self._papel_fixo}\n\n{papel}\n\n{prompt}"
            
            for modelo in self._modelos:
                try:
                    print(f"🔄 Tentando OpenRouter: {modelo}")
                    response = self.client.chat.completions.create(
                        model=modelo,
                        messages=[{"role": "user", "content": prompt_completo[:3000]}],
                        max_tokens=max_tokens,
                        temperature=temperature,
                        extra_headers={
                            "HTTP-Referer": "https://localhost",
                            "X-Title": "4KINGS Debate"
                        }
                    )
                    content = response.choices[0].message.content
                    if content and len(content) > 20:
                        self._modelo_atual = modelo
                        return content
                except Exception as e:
                    print(f"⚠️ OpenRouter ({modelo}): {str(e)[:60]}")
                    continue
            
            raise Exception("Todos os modelos falharam")
        
        return self._executar_com_resiliencia(prompt, _chamada)
    
    def get_nome(self) -> str:
        return self._nome
    
    def get_modelo_atual(self) -> str:
        return self._modelo_atual
    
    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos