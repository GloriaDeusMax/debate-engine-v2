#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
4KINGS V2 - DEBATE ENGINE (Versão Modular)
Ponto de entrada simplificado
"""

import os
import sys

# Adicionar o diretório atual ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
modular_dir = os.path.join(current_dir, 'debate_engine_modular')

# Adicionar ambos os diretórios ao sys.path
if modular_dir not in sys.path:
    sys.path.insert(0, modular_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from debate_engine_modular.main import main
except ImportError as e:
    print(f"⚠️ Erro ao importar o módulo principal: {e}")
    print("\n📁 Estrutura esperada:")
    print("   E:\\estudo\\gemini\\projeto_debate\\")
    print("   ├── debate_engine_modular.py  (este arquivo)")
    print("   └── debate_engine_modular\\")
    print("       ├── __init__.py")
    print("       ├── main.py")
    print("       ├── api\\")
    print("       │   ├── __init__.py")
    print("       │   ├── gemini.py")
    print("       │   ├── groq.py")
    print("       │   └── openrouter.py")
    print("       ├── core\\")
    print("       │   ├── __init__.py")
    print("       │   ├── rate_limiter.py")
    print("       │   ├── circuit_breaker.py")
    print("       │   └── cache.py")
    print("       ├── utils\\")
    print("       │   ├── __init__.py")
    print("       │   └── clean_response.py")
    print("       └── models\\")
    print("           ├── __init__.py")
    print("           └── model_detector.py")
    sys.exit(1)

if __name__ == "__main__":
    main()