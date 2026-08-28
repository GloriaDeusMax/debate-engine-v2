#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
logger.py - Logging estruturado
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional


class DebateLogger:
    """Logger estruturado com rotação de arquivos"""
    
    def __init__(self, log_dir: str = "logs_debates", log_level: str = "INFO"):
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Criar diretório se não existir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configurar logger raiz
        self.logger = logging.getLogger("debate_engine")
        self.logger.setLevel(self.log_level)
        
        # Remover handlers existentes para evitar duplicação
        self.logger.handlers.clear()
        
        # Handler para arquivo (com rotação)
        log_file = os.path.join(log_dir, "debate.log")
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Retorna um logger para um módulo específico."""
        if name:
            return logging.getLogger(f"debate_engine.{name}")
        return self.logger
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def warning(self, msg: str):
        self.logger.warning(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def debug(self, msg: str):
        self.logger.debug(msg)


# Instância global
logger = DebateLogger()