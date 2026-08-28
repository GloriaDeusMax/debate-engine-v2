#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import sys
from typing import Optional

from .core.debate_engine import DebateEngine
from .config import config
from .exceptions import EnvironmentError
from .logger import DebateLogger
from .utils.gerar_tema_auto import gerar_tema_auto


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="4KINGS Debate Engine")
    parser.add_argument("--tema", help="Tema do debate")
    parser.add_argument("--rodadas", type=int, default=None, help="Número de rodadas (padrão: 2)")
    parser.add_argument("--auto", action="store_true", help="Usar modo automático (code review)")
    parser.add_argument("--agentes", nargs="+", help="Lista de agentes (ex: gemini groq)")
    parser.add_argument("--output", help="Arquivo para salvar o histórico")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    logger = DebateLogger(log_dir=config.logs_dir, log_level=config.log_level)
    log = logger.get_logger("cli")

    try:
        from .bootstrap import verificar_dependencias
        verificar_dependencias()

        if args.agentes:
            from .providers import criar_provedores
            providers = criar_provedores()
            filtered = {nome: prov for nome, prov in providers.items() if nome in args.agentes}
            engine = DebateEngine(providers=filtered, max_rounds=args.rodadas)
        else:
            engine = DebateEngine(max_rounds=args.rodadas)

        if args.auto:
            # Usa a função centralizada de geração de tema (com sanitização)
            tema = gerar_tema_auto()
        elif args.tema:
            tema = args.tema
        else:
            print("Digite o tema ou use --auto")
            tema = input("Tema: ")

        log.info(f"Iniciando debate: {tema}")
        engine.run_debate(tema, rodadas=args.rodadas)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(engine.get_historico())
            log.info(f"Histórico salvo em {args.output}")

        resumo = engine.get_resumo()
        print("\n" + "=" * 50)
        print("RESUMO DO DEBATE")
        print("=" * 50)
        if len(resumo) > 2000:
            print(resumo[-2000:])
            print("\n[resumo truncado - use --output para salvar completo]")
        else:
            print(resumo)

        engine.shutdown()
        return 0

    except EnvironmentError as e:
        log.error(f"Erro de configuração: {e}")
        print(f"❌ {e}")
        return 1
    except Exception as e:
        log.error(f"Erro: {e}")
        print(f"❌ Erro: {e}")
        return 1


def main() -> None:
    parser = criar_parser()
    args = parser.parse_args()
    sys.exit(run_cli(args))


if __name__ == "__main__":
    main()