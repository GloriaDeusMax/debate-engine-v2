#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import sys
import time
import logging
import re
from typing import Optional, Dict, List, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.prompt import Prompt

from .interfaces import OrchestratorInterface
from .prompt_builder import prompt_builder
from .config import config
from .exceptions import UIError
from .utils.gerar_tema_auto import gerar_tema_auto, sanitizar_codigo

logger = logging.getLogger(__name__)

CORES_SEGURAS = ["white", "red", "green", "yellow", "blue", "magenta", "cyan",
                 "bright_red", "bright_green", "bright_yellow", "bright_blue",
                 "bright_magenta", "bright_cyan"]

MAX_PROMPT_LEN = 2048
MAX_TEMA_LEN = 500


def sanitize_input(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    if len(text) > MAX_PROMPT_LEN:
        text = text[:MAX_PROMPT_LEN]
    return text.strip()


class DebateUI:
    def __init__(self, orchestrator: OrchestratorInterface):
        self.orchestrator = orchestrator
        self.console = Console(force_terminal=True)

    def run(self):
        try:
            self._run_rich()
        except Exception as e:
            raise UIError(f"Erro na interface Rich: {e}")

    def _get_cor_segura(self, cor: str) -> str:
        if cor in CORES_SEGURAS or cor.startswith("#"):
            return cor
        return "white"

    def _run_rich(self):
        self.console.print(Panel.fit(
            "[bold cyan]🎙️  4KINGS V2 - DEBATE ENGINE[/bold cyan]\n"
            "[dim]Versão 2.6.2 - Sem Debug[/dim]\n"
            "[dim]Digite 'auto' para Code Review automática (com código real)[/dim]",
            border_style="cyan"
        ))

        time.sleep(0.1)
        self._mostrar_agentes()
        time.sleep(0.1)

        tema = self._obter_tema()
        self._executar_debate(tema)
        self._loop_interativo()

    def _mostrar_agentes(self):
        table = Table(title="🤖 Agentes do Debate", box=box.ROUNDED)
        table.add_column("Agente", style="cyan")
        table.add_column("Modelo", style="green")
        table.add_column("Especialidade", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Tokens", style="white")

        for nome, provider in self.orchestrator.providers.items():
            modelo = provider.get_modelo_atual() if hasattr(provider, 'get_modelo_atual') else "N/A"
            emoji = prompt_builder.get_emoji(nome)
            cor = self._get_cor_segura(prompt_builder.get_cor(nome))
            display_name = nome.replace("_", " ").title()

            if hasattr(provider, '_especialidades'):
                especialidade = provider._especialidades.get(modelo, "Assistente especializado.")
            else:
                especialidade = prompt_builder.get_papel(nome)

            max_tokens = getattr(config, 'max_tokens_por_agente', {}).get(nome, 800)
            if 'ollama' in nome:
                max_tokens = getattr(config, 'max_tokens_por_agente', {}).get('ollama', 400)

            table.add_row(
                f"{emoji} {display_name}",
                modelo[:25] + ("..." if len(modelo) > 25 else ""),
                especialidade[:30] + ("..." if len(especialidade) > 30 else ""),
                "✅ Ativo",
                f"{max_tokens}"
            )

        self.console.print(table)

    def _obter_tema(self) -> str:
        self.console.print()
        tema = Prompt.ask("\n[bold yellow]📝 Tema do debate (ou 'auto'):[/bold yellow]")
        if not tema:
            raise UIError("Tema não pode ser vazio!")

        tema = sanitize_input(tema)
        if not tema.strip():
            raise UIError("Tema inválido após sanitização!")

        if len(tema) > MAX_TEMA_LEN:
            tema = tema[:MAX_TEMA_LEN]
            self.console.print(f"[yellow]⚠️ Tema truncado para {MAX_TEMA_LEN} caracteres.[/yellow]")

        if tema.lower() == "auto":
            tema = gerar_tema_auto()
            self.console.print("\n[bold cyan]🤖 Modo AUTO - Code Review com código real![/bold cyan]")

        return tema

    def _executar_debate(self, tema: str):
        max_rounds = getattr(config, 'max_rounds_padrao', 3)
        self.console.print(f"\n[green]▶ Iniciando debate com {max_rounds} rodada(s)...[/green]")

        self.console.print(Panel(tema, title="Tema", border_style="cyan"))

        for rodada in range(1, max_rounds + 1):
            self.console.print(f"\n[bold cyan]======= RODADA {rodada} =======[/bold cyan]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Gerando respostas...", total=None)
                respostas = self.orchestrator.run_round(tema, rodada)
                progress.update(task, completed=True)

            self._exibir_respostas(respostas, rodada)

        self._mostrar_resumo()

    def _exibir_respostas(self, respostas: dict, rodada: int):
        self.console.print(f"\n[bold]📢 Respostas da Rodada {rodada}:[/bold]")
        for nome, resposta in respostas.items():
            if resposta.startswith("[Erro") or resposta.startswith("[Circuit"):
                self.console.print(f"[red]{nome}: {resposta[:100]}[/red]")
                continue

            emoji = prompt_builder.get_emoji(nome)
            cor = self._get_cor_segura(prompt_builder.get_cor(nome))
            display_name = nome.replace("_", " ").title()

            resposta_exib = resposta[:800] + ("..." if len(resposta) > 800 else "")
            self.console.print(Panel(
                Markdown(resposta_exib),
                title=f"[bold {cor}]{emoji} {display_name}[/bold {cor}]",
                border_style=cor
            ))
            self.console.print()

    def _loop_interativo(self):
        self.console.print("\n[bold green]✅ Debate concluído! Participe:[/bold green]")
        self.console.print("Digite sua mensagem para os agentes responderem, ou 'sair' para encerrar\n")

        while True:
            mensagem = Prompt.ask("[bold yellow]💭 Você:[/bold yellow]")
            if mensagem.lower() in ['sair', 'exit', 'quit']:
                break

            mensagem = sanitize_input(mensagem)
            if not mensagem:
                continue

            self.console.print("\n[bold]🤖 Agentes respondendo...[/bold]")
            respostas = self.orchestrator.continuar_chat(mensagem, incluir_historico=True)
            self._exibir_respostas_continuacao(respostas)

    def _exibir_respostas_continuacao(self, respostas: dict):
        for nome, resposta in respostas.items():
            if resposta.startswith("[Erro") or resposta.startswith("[Circuit"):
                self.console.print(f"[red]{nome}: {resposta[:100]}[/red]")
                continue

            emoji = prompt_builder.get_emoji(nome)
            cor = self._get_cor_segura(prompt_builder.get_cor(nome))
            display_name = nome.replace("_", " ").title()

            self.console.print(Panel(
                Markdown(resposta[:500] + ("..." if len(resposta) > 500 else "")),
                title=f"[bold {cor}]{emoji} {display_name}[/bold {cor}]",
                border_style=cor
            ))
            self.console.print()

    def _mostrar_resumo(self):
        resumo = self.orchestrator.get_debate_summary()
        self.console.print(Panel(
            Markdown(resumo[-500:]) if resumo else "Sem histórico.",
            title="📊 Resumo Final",
            border_style="green"
        ))

        # Cache desativado na UI por enquanto.
        # Para reativar: descomente a linha abaixo quando o cache estiver em uso real.
        # self._mostrar_cache_stats()

    def _mostrar_cache_stats(self):
        """Exibe estatísticas do cache de todos os provedores."""
        table = Table(title="📊 Estatísticas do Cache")
        table.add_column("Provedor", style="cyan")
        table.add_column("Tamanho", style="white")
        table.add_column("Hits", style="white")
        table.add_column("Misses", style="white")
        table.add_column("Hit Rate", style="white")

        for nome, provider in self.orchestrator.providers.items():
            if hasattr(provider, 'cache'):
                cache = provider.cache
                tamanho = len(cache.cache) if hasattr(cache, 'cache') else 0
                max_size = getattr(cache, 'max_size', 100)
                hits = cache.hits if hasattr(cache, 'hits') else 0
                misses = cache.misses if hasattr(cache, 'misses') else 0
                total = hits + misses
                hit_rate = f"{(hits / total * 100):.1f}%" if total > 0 else "0.0%"
                table.add_row(
                    nome.replace("_", " ").title(),
                    f"{tamanho}/{max_size}",
                    str(hits),
                    str(misses),
                    hit_rate
                )
            else:
                table.add_row(nome.replace("_", " ").title(), "N/A", "0", "0", "0.0%")

        self.console.print(table)

    # Métodos de compatibilidade (não são mais usados, mas mantidos para não quebrar imports antigos)
    def _sanitizar_codigo(self, texto: str) -> str:
        return sanitizar_codigo(texto)

    def _gerar_tema_auto(self) -> str:
        return gerar_tema_auto()


if __name__ == "__main__":
    from .orchestrator import RealOrchestrator
    with RealOrchestrator() as orch:
        ui = DebateUI(orch)
        ui.run()