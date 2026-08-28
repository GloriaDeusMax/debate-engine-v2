#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Dict, Optional

from .gemini import GeminiProvider
from .groq import GroqProvider
from .openrouter import OpenRouterProvider


class ProviderFactory:
    """Fábrica de provedores (Abstract Factory Pattern)"""
    
    def __init__(self):
        self._providers: Dict[str, object] = {}
    
    def create_providers(self, gemini_key: Optional[str] = None, 
                         groq_key: Optional[str] = None, 
                         openrouter_key: Optional[str] = None) -> Dict[str, object]:
        """Cria todos os provedores disponíveis"""
        
        # Gemini
        if gemini_key:
            try:
                self._providers['gemini'] = GeminiProvider(gemini_key)
            except Exception as e:
                print(f"⚠️ Gemini: {e}")
        else:
            print("ℹ️ Gemini: chave não configurada (opcional)")
        
        # Groq
        if groq_key:
            try:
                self._providers['groq'] = GroqProvider(groq_key)
            except Exception as e:
                print(f"⚠️ Groq: {e}")
        else:
            print("ℹ️ Groq: chave não configurada (opcional)")
        
        # OpenRouter
        if openrouter_key:
            try:
                self._providers['openrouter'] = OpenRouterProvider(openrouter_key)
            except Exception as e:
                print(f"⚠️ OpenRouter: {e}")
        else:
            print("ℹ️ OpenRouter: chave não configurada (opcional)")
        
        return self._providers