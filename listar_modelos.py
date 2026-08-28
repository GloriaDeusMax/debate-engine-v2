#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Lista todos os modelos disponíveis - Versão corrigida para Gemini"""

import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from google import genai

print("="*60)
print("📋 MODELOS DISPONÍVEIS")
print("="*60)

# Groq
print("\n🔵 GROQ:")
try:
    client = OpenAI(api_key=os.environ.get('GROQ_API_KEY'), base_url="https://api.groq.com/openai/v1")
    modelos = client.models.list()
    for m in modelos.data:
        print(f"  - {m.id}")
except Exception as e:
    print(f"  ❌ Erro: {e}")

# Gemini - CORRIGIDO
print("\n🟢 GEMINI:")
try:
    client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
    # Usar o método correto para listar modelos
    modelos = client.models.list()
    
    # Filtrar apenas modelos Gemini
    for m in modelos:
        nome = m.name if hasattr(m, 'name') else str(m)
        if 'gemini' in nome.lower():
            print(f"  - {nome}")
        else:
            print(f"  (outro) - {nome}")
            
    print(f"\n✅ Total de modelos encontrados: {len(modelos)}")
    
except Exception as e:
    print(f"  ❌ Erro: {e}")
    print("  💡 Tentando método alternativo...")
    
    try:
        # Método alternativo
        client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
        modelos = client.models.list()
        for m in modelos:
            try:
                print(f"  - {m.name}")
            except:
                print(f"  - {m}")
    except Exception as e2:
        print(f"  ❌ Erro alternativo: {e2}")