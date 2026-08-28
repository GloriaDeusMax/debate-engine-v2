#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
main.py - Ponto de entrada do 4KINGS Debate Engine
Versão melhorada com logging e organização
"""

import os
import sys
import logging
from typing import Optional

# Configurar logging ANTES de tudo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Adicionar diretório atual ao path (mantido por enquanto)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info(".env carregado com sucesso")
except ImportError:
    logger.warning("python-dotenv não instalado. Use: pip install python-dotenv")

from debate_engine_ui import DebateUI


# ==============================================================================
# FUNÇÕES DE VERIFICAÇÃO
# ==============================================================================

def verificar_dependencias() -> bool:
    """Verifica se as dependências necessárias estão instaladas."""
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
                __import__('google')
            elif modulo == 'openai':
                __import__('openai')
            elif modulo == 'dotenv':
                __import__('dotenv')
            logger.info(f"✅ {pacote} instalado")
        except ImportError:
            logger.error(f"❌ {pacote} não instalado")
            faltando.append(pacote)
    
    if faltando:
        logger.error(f"Dependências faltando: {', '.join(faltando)}")
        logger.info(f"Instale com: pip install {' '.join(faltando)}")
        return False
    
    return True


def verificar_chaves() -> bool:
    """Verifica se as chaves de API estão configuradas."""
    gemini_key = os.environ.get('GEMINI_API_KEY')
    groq_key = os.environ.get('GROQ_API_KEY')
    openrouter_key = os.environ.get('OPENROUTER_API_KEY')
    
    logger.info("Verificando chaves de API...")
    
    status = []
    if gemini_key and len(gemini_key) > 10:
        status.append(f"Gemini: {gemini_key[:10]}... (OK)")
    else:
        status.append("Gemini: ❌ ausente ou inválida")
    
    if groq_key and len(groq_key) > 10:
        status.append(f"Groq: {groq_key[:10]}... (OK)")
    else:
        status.append("Groq: ❌ ausente ou inválida")
    
    if openrouter_key and len(openrouter_key) > 10:
        status.append(f"OpenRouter: {openrouter_key[:10]}... (OK)")
    else:
        status.append("OpenRouter: ℹ️ não configurado (opcional)")
    
    for s in status:
        logger.info(s)
    
    if not gemini_key and not groq_key:
        logger.error("Nenhuma chave de API válida encontrada!")
        logger.info("Crie um arquivo .env com:")
        logger.info("  GEMINI_API_KEY=sua_chave_aqui")
        logger.info("  GROQ_API_KEY=sua_chave_aqui")
        return False
    
    return True


def criar_pasta_logs() -> bool:
    """Cria a pasta de logs se não existir."""
    logs_dir = os.path.join(os.getcwd(), "logs_debates")
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
            logger.info(f"Pasta de logs criada: {logs_dir}")
        except Exception as e:
            logger.error(f"Erro ao criar pasta de logs: {e}")
            return False
    return True


# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================

def main():
    """Função principal do programa."""
    logger.info("=" * 50)
    logger.info("🚀 INICIANDO 4KINGS DEBATE ENGINE")
    logger.info("=" * 50)
    
    # Verificar dependências
    if not verificar_dependencias():
        sys.exit(1)
    
    # Criar pasta de logs
    if not criar_pasta_logs():
        sys.exit(1)
    
    # Verificar chaves
    if not verificar_chaves():
        sys.exit(1)
    
    # Importar orquestrador
    try:
        from orchestrator_real import RealOrchestrator
        logger.info("Orquestrador carregado com sucesso")
    except ImportError as e:
        logger.error(f"Erro ao importar orquestrador: {e}")
        sys.exit(1)
    
    # Criar orquestrador
    try:
        orchestrator = RealOrchestrator()
    except Exception as e:
        logger.error(f"Erro ao criar orquestrador: {e}")
        sys.exit(1)
    
    # Verificar provedores
    if not orchestrator.providers:
        logger.error("Nenhum provedor configurado!")
        sys.exit(1)
    
    logger.info(f"Provedores ativos: {', '.join(orchestrator.providers.keys())}")
    logger.info("=" * 50)
    
    # Executar UI
    try:
        ui = DebateUI(orchestrator)
        ui.run()
    except KeyboardInterrupt:
        logger.info("Encerrado pelo usuário.")
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()