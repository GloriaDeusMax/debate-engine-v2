#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
healthcheck.py - Verificações de saúde do sistema
Separado do main.py para melhor organização
"""

import os
import sys
import logging
from typing import List, Tuple, Dict

from .config import config
from .exceptions import EnvironmentError

logger = logging.getLogger(__name__)


def verificar_dependencias() -> Tuple[bool, List[str]]:
    """
    Verifica se as dependências necessárias estão instaladas.
    
    Returns:
        Tuple[bool, List[str]]: (sucesso, lista de faltando)
    
    Raises:
        EnvironmentError: Se dependências críticas estiverem faltando
    """
    dependencias = {
        'google': 'google-generativeai',
        'openai': 'openai',
        'dotenv': 'python-dotenv',
    }
    
    logger.info("Verificando dependências...")
    faltando = []
    
    for modulo, pacote in dependencias.items():
        try:
            if modulo == 'google':
                import google
            elif modulo == 'openai':
                import openai
            elif modulo == 'dotenv':
                import dotenv
            logger.info(f"✅ {pacote} instalado")
        except ImportError:
            logger.error(f"❌ {pacote} não instalado")
            faltando.append(pacote)
    
    if faltando:
        logger.error(f"Dependências faltando: {', '.join(faltando)}")
        logger.info(f"Instale com: pip install {' '.join(faltando)}")
        raise EnvironmentError(f"Dependências faltando: {', '.join(faltando)}")
    
    return True, []


def verificar_chaves() -> Tuple[bool, Dict]:
    """
    Verifica se as chaves de API estão configuradas.
    ⚠️ NUNCA expõe as chaves nos logs (segurança)
    
    Returns:
        Tuple[bool, dict]: (sucesso, status das chaves)
    
    Raises:
        EnvironmentError: Se nenhuma chave obrigatória estiver configurada
    """
    logger.info("Verificando chaves de API...")
    
    # ✅ NUNCA mostrar chaves nos logs
    has_gemini = bool(config.gemini_api_key and len(config.gemini_api_key) > 10)
    has_groq = bool(config.groq_api_key and len(config.groq_api_key) > 10)
    has_openrouter = bool(config.openrouter_api_key and len(config.openrouter_api_key) > 10)
    
    status = {
        'gemini': {
            'configurada': has_gemini,
            'mensagem': '✅ OK' if has_gemini else '❌ ausente',
        },
        'groq': {
            'configurada': has_groq,
            'mensagem': '✅ OK' if has_groq else '❌ ausente',
        },
        'openrouter': {
            'configurada': has_openrouter,
            'mensagem': '✅ OK' if has_openrouter else 'ℹ️ opcional',
        },
    }
    
    # Log seguro - apenas status, nunca chaves
    for nome, st in status.items():
        if st['configurada']:
            logger.info(f"{nome.capitalize()}: ✅ OK")
        else:
            if nome == 'openrouter':
                logger.info(f"{nome.capitalize()}: ℹ️ opcional")
            else:
                logger.error(f"{nome.capitalize()}: ❌ ausente")
    
    # Verificar se tem pelo menos uma chave obrigatória
    tem_chave = has_gemini or has_groq
    
    if not tem_chave:
        logger.error("Nenhuma chave de API obrigatória encontrada!")
        logger.info("Crie um arquivo .env com:")
        logger.info("  GEMINI_API_KEY=sua_chave_aqui")
        logger.info("  GROQ_API_KEY=sua_chave_aqui")
        raise EnvironmentError("Nenhuma chave de API obrigatória configurada")
    
    return True, status


def criar_pasta_logs() -> bool:
    """Cria a pasta de logs se não existir."""
    logs_dir = os.path.join(os.getcwd(), config.logs_dir)
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
            logger.info(f"Pasta de logs criada: {logs_dir}")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar pasta de logs: {e}")
            raise EnvironmentError(f"Erro ao criar pasta de logs: {e}")
    return True


def verificar_ambiente() -> Tuple[bool, Dict]:
    """
    Verifica todo o ambiente (dependências, chaves, pastas).
    
    Returns:
        Tuple[bool, dict]: (sucesso, relatório completo)
    
    Raises:
        EnvironmentError: Se alguma verificação falhar
    """
    relatorio = {
        'dependencias': {},
        'chaves': {},
        'pastas': {},
    }
    
    # Verificar dependências
    deps_ok, deps_faltando = verificar_dependencias()
    relatorio['dependencias'] = {
        'sucesso': deps_ok,
        'faltando': deps_faltando,
    }
    
    # Verificar chaves
    chaves_ok, chaves_status = verificar_chaves()
    relatorio['chaves'] = chaves_status
    
    # Verificar pastas
    pasta_ok = criar_pasta_logs()
    relatorio['pastas']['logs'] = '✅ OK' if pasta_ok else '❌ erro'
    
    sucesso = deps_ok and chaves_ok and pasta_ok
    
    if not sucesso:
        raise EnvironmentError(f"Ambiente não está pronto: {relatorio}")
    
    return sucesso, relatorio


if __name__ == "__main__":
    # Teste rápido
    print("🧪 Testando healthcheck...")
    try:
        sucesso, relatorio = verificar_ambiente()
        print(f"✅ Sucesso: {sucesso}")
        print(f"📊 Relatório: {relatorio}")
    except EnvironmentError as e:
        print(f"❌ Erro: {e}")