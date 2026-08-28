#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testa quais modelos da NVIDIA NIM estão disponíveis no seu plano gratuito.
Execute: python testar_nvidia.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("NVIDIA_API_KEY", "")

if not api_key:
    print("❌ NVIDIA_API_KEY não encontrada no .env")
    exit(1)

# Lista de modelos candidatos (nomes retornados na listagem)
modelos = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "deepseek-ai/deepseek-v4-flash-0731",
    "deepseek-ai/deepseek-coder-6.7b-instruct",
    "meta/llama2-70b",
    "mistralai/mistral-7b-instruct-v0.3",
    "google/gemma-3-12b-it",
    "nvidia/nemotron-3-nano-30b-a3b",
    "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/llama-3.1-nemotron-51b-instruct",
    "ai21labs/jamba-1.5-large-instruct",
    "writer/palmyra-creative-122b",
]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print("🔍 Testando modelos gratuitos da NVIDIA...\n")

for modelo in modelos:
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": "Oi, tudo bem? Responda curto."}],
        "max_tokens": 20,
        "temperature": 0.1
    }
    try:
        r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
                          json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            resposta = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ {modelo} → FUNCIONOU! Resposta: {resposta[:50]}")
        elif r.status_code == 404:
            print(f"❌ {modelo} → 404 (não existe ou sem acesso)")
        elif r.status_code == 401:
            print(f"❌ {modelo} → 401 (chave inválida?)")
            break
        else:
            print(f"⚠️ {modelo} → {r.status_code} ({r.text[:80]})")
    except Exception as e:
        print(f"⚠️ {modelo} → Erro: {str(e)[:60]}")

print("\n✅ Teste concluído!")