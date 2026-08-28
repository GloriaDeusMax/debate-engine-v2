#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
import os
import sys
from pathlib import Path
from typing import Tuple

from .config import config
from .logger import DebateLogger
from .orchestrator import RealOrchestrator
from .exceptions import EnvironmentError


def verificar_dependencias() -> None:
    """Verifica se as bibliotecas essenciais estão instaladas e orienta como instalar."""
    dependencias = {
        "google.genai": "google-generativeai",
        "openai": "openai",
        "dotenv": "python-dotenv",
        "rich": "rich",
        "requests": "requests",
    }
    faltantes = []
    for modulo, pip_name in dependencias.items():
        try:
            importlib.import_module(modulo)
        except ImportError:
            faltantes.append(pip_name)

    if faltantes:
        lista = ", ".join(faltantes)
        raise EnvironmentError(
            f"Bibliotecas faltando: {lista}.\n"
            f"Instale com: pip install {lista}"
        )


def setup_logging() -> DebateLogger:
    """Configura o logger."""
    if not os.path.exists(config.logs_dir):
        os.makedirs(config.logs_dir, exist_ok=True)  # evitar FileExistsError
    return DebateLogger(log_dir=config.logs_dir, log_level=config.log_level)


def bootstrap() -> Tuple[DebateLogger, RealOrchestrator]:
    """Inicializa logger e orquestrador."""
    logger = setup_logging()

    # Verificar dependências
    try:
        verificar_dependencias()
        logger.get_logger("bootstrap").info("Dependências verificadas com sucesso.")
    except EnvironmentError as e:
        print(f"❌ {e}")
        raise

    # Verificar .env
    project_dir = Path(__file__).resolve().parent.parent
    env_path = project_dir / ".env"
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        logger.get_logger("bootstrap").info(f"Arquivo .env carregado de {env_path}")
    else:
        logger.get_logger("bootstrap").warning("Arquivo .env não encontrado. Usando variáveis de ambiente do sistema.")

    # Criar provedores
    from .providers import criar_provedores
    providers = criar_provedores()
    if not providers:
        raise EnvironmentError("Nenhum provedor configurado. Verifique suas chaves de API ou instale o Ollama.")

    logger.get_logger("bootstrap").info(f"Provedores encontrados: {', '.join(providers.keys())}")

    # Criar orquestrador
    try:
        orchestrator = RealOrchestrator(providers=providers)
    except Exception as e:
        logger.get_logger("bootstrap").error(f"Erro ao criar orquestrador: {e}")
        raise

    logger.get_logger("bootstrap").info("Bootstrap concluído.")
    return logger, orchestrator