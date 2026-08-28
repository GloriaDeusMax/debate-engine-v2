#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List
from openai import OpenAI

from .base import BaseProvider
from ..models.model_detector import ModelDetector


class GroqProvider(BaseProvider):
    """Provedor Groq com Strategy Pattern"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self._nome = "groq"
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        
        # Detectar modelos
        detector = ModelDetector('groq')
        self._modelos = detector.detectar(api_key)
        self._modelo_atual = self._modelos[0] if self._modelos else "openai/gpt-oss-120b"
        
        self._papel_fixo = """Você é um engenheiro de software Python sênior.

REGRAS:
- NUNCA se apresente ou se cumprimente
- Foque em soluções práticas e código
- Use listas e exemplos concretos
- Responda em Português do Brasil

FORMATO:
## Título da análise
- Ponto 1
- Ponto 2
- Código exemplo"""
        
        print(f"✅ Groq configurado - modelos: {', '.join(self._modelos[:3])}...")
    
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Executa chamada ao Groq"""
        
        def _chamada():
            prompt_completo = f"{self._papel_fixo}\n\n{papel}\n\n{prompt}"
            
            for modelo in self._modelos:
                try:
                    print(f"🔄 Tentando Groq: {modelo}")
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
                    print(f"⚠️ Groq ({modelo}): {str(e)[:60]}")
                    continue
            
            raise Exception("Todos os modelos falharam")
        
        return self._executar_com_resiliencia(prompt, _chamada)
    
    def get_nome(self) -> str:
        return self._nome
    
    def get_modelo_atual(self) -> str:
        return self._modelo_atual
    
    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos