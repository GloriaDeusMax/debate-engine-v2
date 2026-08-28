#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Gera tema para Code Review automática com os arquivos reais"""

import os

def gerar_tema_auto_real() -> str:
    """Gera tema com os arquivos reais do projeto"""
    try:
        codigo_completo = ""
        arquivos_encontrados = []
        
        # Lista de arquivos para revisar
        arquivos_para_revisar = [
            'main.py',
            'orchestrator_real.py',
            'debate_engine_ui.py',
            'config.py',
            'providers.py',
        ]
        
        for arquivo in arquivos_para_revisar:
            if os.path.exists(arquivo):
                with open(arquivo, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    linhas = conteudo.split('\n')
                    linhas_limitadas = linhas[:80]  # Pega 80 linhas de cada
                    if len(linhas) > 80:
                        linhas_limitadas.append(f"... [TRUNCADO - {len(linhas) - 80} linhas] ...")
                    
                    codigo_completo += f"\n\n# ===== {arquivo} =====\n"
                    codigo_completo += '\n'.join(linhas_limitadas)
                    arquivos_encontrados.append(arquivo)
        
        if not arquivos_encontrados:
            return "Nenhum arquivo encontrado para revisão."
        
        tema = f"""# CODE REVIEW AUTOMÁTICA DO 4KINGS DEBATE ENGINE

## Arquivos para Revisão ({len(arquivos_encontrados)}):
{', '.join(arquivos_encontrados)}

## Código:

```python
{codigo_completo}