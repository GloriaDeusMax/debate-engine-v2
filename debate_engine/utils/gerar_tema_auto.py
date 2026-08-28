#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Módulo centralizado para gerar tema de Code Review automático.
Contém a lógica de leitura de arquivos e sanitização de segredos,
usada tanto pela UI interativa (ui.py) quanto pela CLI (cli.py).

Este módulo não depende de nenhuma instância ou estado - são funções puras.
"""

from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Lista de arquivos principais (exclui .env e qualquer sensível)
ARQUIVOS_PRINCIPAIS = [
    "main.py",
    "bootstrap.py",
    "orchestrator.py",
    "ui.py",
    "config.py",
    "prompt_builder.py",
    "providers/base.py",
    "providers/factory.py",
    "providers/gemini.py",
    "providers/groq.py",
    "providers/openrouter.py",
    "providers/nvidia.py",
    "providers/ollama.py",
    "core/rate_limiter.py",
    "core/circuit_breaker.py",
    "core/cache.py",
]

# Limites para não estourar contexto
LIMITE_CARACTERES_POR_ARQUIVO = 1200
LIMITE_TOTAL_CARACTERES = 12000


def sanitizar_codigo(texto: str) -> str:
    """
    Remove valores sensíveis antes de enviar o código para LLMs externos.
    Mascara padrões como chaves de API, tokens, segredos e senhas.
    Retorna o texto sanitizado e registra um aviso se algo foi mascarado.
    """
    original = texto
    padrao_segredos = (
        r'(?i)(api[_-]?key|token|secret|password|passwd|pwd|senha)'
        r'(\s*:\s*\w+\s*)?\s*=\s*["\'][^"\']+["\']'
    )
    texto = re.sub(padrao_segredos, r'\1 = "***MASKED***"', texto)
    texto = re.sub(r'sk-[a-zA-Z0-9]{20,}', '***MASKED_KEY***', texto)
    texto = re.sub(r'AIza[a-zA-Z0-9_-]{30,}', '***MASKED_KEY***', texto)

    if texto != original:
        logger.warning("🔒 Sanitização aplicada: valores sensíveis foram mascarados antes do envio ao LLM.")
    return texto


def gerar_tema_auto(base_path: Optional[Path] = None) -> str:
    """
    Gera o tema de Code Review lendo o código real do projeto (sanitizado).

    Args:
        base_path: Caminho base do pacote (por padrão, sobe um nível de utils/ para debate_engine/).

    Returns:
        String com o tema contendo trechos de código.
    """
    try:
        # Se base_path não for fornecido, calcula o diretório raiz do pacote
        if base_path is None:
            # Este arquivo está em debate_engine/utils/gerar_tema_auto.py
            # Subimos dois níveis: utils/ -> debate_engine/
            base_path = Path(__file__).resolve().parent.parent

        codigo_total = ""

        for arquivo in ARQUIVOS_PRINCIPAIS:
            # Proteção extra: nunca ler .env ou arquivos de ambiente
            if arquivo == ".env" or arquivo.endswith(".env"):
                continue

            caminho = base_path / arquivo
            if not caminho.exists():
                continue

            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    conteudo = f.read()

                # Sanitiza o conteúdo antes do truncamento
                conteudo = sanitizar_codigo(conteudo)

                # Trunca por arquivo
                if len(conteudo) > LIMITE_CARACTERES_POR_ARQUIVO:
                    conteudo = conteudo[:LIMITE_CARACTERES_POR_ARQUIVO]
                    conteudo += "\n# ... (truncado por tamanho)\n"

                codigo_total += f"# ==== {arquivo} ====\n{conteudo}\n\n"

                if len(codigo_total) >= LIMITE_TOTAL_CARACTERES:
                    codigo_total = codigo_total[:LIMITE_TOTAL_CARACTERES]
                    codigo_total += "\n# ... (truncado por limite total)\n"
                    break
            except Exception as e:
                logger.warning(f"Não foi possível ler {arquivo}: {e}")
                continue

        tema = "# CODE REVIEW DO 4KINGS DEBATE ENGINE V2 (com código real)\n\n"
        tema += "## Contexto\n"
        tema += "Sistema multi-agente de debate entre LLMs.\n\n"
        tema += "## Código Real do Projeto (trechos sanitizados):\n"
        tema += f"```python\n{codigo_total}\n```\n\n"
        tema += "## Análise Solicitada:\n"
        tema += "1. **Arquitetura**: coesão, acoplamento, padrões.\n"
        tema += "2. **Tratamento de erros**: fallbacks, circuit breakers.\n"
        tema += "3. **Segurança**: mascaramento de chaves, sanitização.\n"
        tema += "4. **Eficiência**: cache, rate limit.\n"
        tema += "5. **Manutenibilidade**: type hints, docstrings.\n\n"
        tema += "Responda em português do Brasil, de forma clara e objetiva, apontando problemas específicos do código mostrado, sem inventar problemas que não estão no trecho."
        return tema
    except Exception as e:
        return f"Code Review do sistema (erro ao gerar tema: {e})"