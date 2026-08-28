#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List
from openai import OpenAI

from .base import BaseProvider


class NvidiaProvider(BaseProvider):
    """Provedor NVIDIA NIM - DeepSeek V4 Flash"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self._nome = "nvidia"
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        
        self._modelos = [
            'deepseek-ai/deepseek-v4-flash',
            'nvidia/nemotron-4-34b-instruct'
        ]
        self._modelo_atual = self._modelos[0]
        self.rate_limiter.max_calls = 40  # 40 req/min
        
        self._papel_fixo = """Você é um especialista em performance computacional e otimização.

REGRAS:
- NUNCA se apresente ou se cumprimente
- Foque em eficiência, escalabilidade e otimização
- Use dados e métricas para embasar suas análises
- Responda em Português do Brasil

FORMATO:
## Título da análise
- Métrica 1
- Métrica 2
- Recomendação"""
        
        print(f"✅ NVIDIA NIM configurado - modelos: {', '.join(self._modelos[:3])}...")
    
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Executa chamada ao NVIDIA NIM"""
        
        def _chamada():
            prompt_completo = f"{self._papel_fixo}\n\n{papel}\n\n{prompt}"
            
            for modelo in self._modelos:
                try:
                    print(f"🔄 Tentando NVIDIA NIM: {modelo}")
                    response = self.client.chat.completions.create(
                        model=modelo,
                        messages=[{"role": "user", "content": prompt_completo[:3000]}],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    content = response.choices[0].message.content
                    if content and len(content) > 20:
                        self._modelo_atual = modelo
                        return content
                except Exception as e:
                    print(f"⚠️ NVIDIA NIM ({modelo}): {str(e)[:60]}")
                    if "429" in str(e):
                        print("⏳ Rate limit, aguardando 5s...")
                        time.sleep(5)
                    continue
            
            raise Exception("Todos os modelos falharam")
        
        return self._executar_com_resiliencia(prompt, _chamada)
    
    def get_nome(self) -> str:
        return self._nome
    
    def get_modelo_atual(self) -> str:
        return self._modelo_atual
    
    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos