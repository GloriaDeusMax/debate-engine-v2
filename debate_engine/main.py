#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from typing import Optional

from .cli import run_cli, criar_parser
from .bootstrap import bootstrap
from .exceptions import EnvironmentError


def main() -> int:
    """Ponto de entrada principal."""
    parser = criar_parser()
    args = parser.parse_args()

    # Verificar se algum argumento específico de CLI foi passado
    # Usamos "is not None" em vez de any() para evitar bugs com valores falsos (ex: --rodadas 0)
    modo_cli = any(
        getattr(args, field) is not None
        for field in ("tema", "auto", "agentes", "rodadas", "output")
    )

    # Se tiver argumentos, usa CLI
    if modo_cli:
        return run_cli(args)

    # Caso contrário, usa UI interativa
    try:
        logger, orchestrator = bootstrap()
        from .ui import DebateUI
        with orchestrator:
            ui = DebateUI(orchestrator)
            ui.run()
        return 0
    except EnvironmentError as e:
        print(f"❌ Erro de ambiente: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Erro inesperado: {e}", file=sys.stderr)
        # Em produção, logar exceção completa
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())