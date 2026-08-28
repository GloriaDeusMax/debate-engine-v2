#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List
from google import genai

from .base import BaseProvider
from ..models.model_detector import ModelDetector


class GeminiProvider(BaseProvider):
    """Provedor Gemini com Strategy Pattern"""
    
    def __init__(self, api_key: str):
        super().__init__()
        self._nome = "gemini"
        self.client = genai.Client(api_key=api_key)
        
        # Detectar modelos
        detector = ModelDetector('gemini')
        self._modelos = detector.detectar(api_key)
        self._modelo_atual = self._modelos[0] if self._modelos else "gemini-3.6-flash"
        
        self._papel_fixo = """Você é um especialista em arquitetura de software.

REGRAS:
- NUNCA se apresente ou se cumprimente
- Seja direto e objetivo
- Use títulos (##) para organizar a resposta
- Dê exemplos práticos de código
- Responda em Português do Brasil

FORMATO:
## Título da análise
Conteúdo direto..."""
        
        print(f"✅ Gemini configurado - modelos: {', '.join(self._modelos[:3])}...")
    
    def call(self, prompt: str, papel: str, max_tokens: int = 800, temperature: float = 0.3) -> str:
        """Executa chamada ao Gemini"""
        
        def _chamada():
            prompt_completo = f"{self._papel_fixo}\n\n{papel}\n\n{prompt}"
            
            for modelo in self._modelos:
                try:
                    print(f"🔄 Tentando Gemini: {modelo}")
                    response = self.client.models.generate_content(
                        model=modelo,
                        contents=prompt_completo[:2500]
                    )
                    if response.text and len(response.text) > 30:
                        self._modelo_atual = modelo
                        return response.text
                except Exception as e:
                    print(f"⚠️ Gemini ({modelo}): {str(e)[:60]}")
                    continue
            
            raise Exception("Todos os modelos falharam")
        
        return self._executar_com_resiliencia(prompt, _chamada)
    
    def get_nome(self) -> str:
        return self._nome
    
    def get_modelo_atual(self) -> str:
        return self._modelo_atual
    
    def get_modelos_disponiveis(self) -> List[str]:
        return self._modelos