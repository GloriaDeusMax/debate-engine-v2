#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
debate_engine_ui.py - Interface de Usuário do 4KINGS Debate Engine
Gerencia a interação com o usuário, exibição de resultados e entrada de dados
Versão unificada - não requer estrutura de pastas
"""

import os
import sys
import time
import re
from typing import Optional, Dict, List, Tuple

# Tentar importar Rich para UI melhorada
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box
    from rich.prompt import Prompt
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class DebateUI:
    """
    Interface de usuário para o debate.
    
    Gerencia:
    - Exibição de status dos agentes
    - Entrada de temas
    - Exibição de respostas em tempo real
    - Resultados finais
    - Modo Auto (Code Review)
    """
    
    def __init__(self, orchestrator):
        """
        Inicializa a UI.
        
        Args:
            orchestrator: Instância do DebateOrchestrator
        """
        self.orchestrator = orchestrator
        self.console = Console() if RICH_AVAILABLE else None
        self.historico = []
        self.agentes_ativos = []
        
        # Cores para cada agente
        self.cores = {
            'gemini': 'blue',
            'groq': 'green',
            'sambanova': 'orange1',
            'nvidia': 'cyan',
            'liquid': 'magenta',
            'thinking': 'purple',
            'cohere': 'yellow',
            'zai': 'red',
            'poolside': 'white',
            'curinga': 'magenta',
        }
        
        # Emojis para cada agente
        self.emoji = {
            'gemini': '🔬',
            'groq': '⚡',
            'sambanova': '🔍',
            'nvidia': '🚀',
            'liquid': '💧',
            'thinking': '🧠',
            'cohere': '💻',
            'zai': '🎯',
            'poolside': '🏊',
            'curinga': '🔄',
        }
        
        # Garantir que a pasta de logs existe
        self._ensure_logs_dir()
    
    def _ensure_logs_dir(self):
        """Garante que a pasta de logs existe."""
        logs_dir = os.path.join(os.getcwd(), "logs_debates")
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir)
                print(f"📁 Pasta de logs criada: {logs_dir}")
            except Exception as e:
                print(f"⚠️ Erro ao criar pasta de logs: {e}")
    
    def run(self):
        """Executa a interface principal."""
        if RICH_AVAILABLE:
            self._run_rich()
        else:
            self._run_basic()
    
    # ========================================================================
    # INTERFACE RICH (UI Avançada)
    # ========================================================================
    
    def _run_rich(self):
        """Interface com Rich - UI avançada."""
        self._mostrar_cabecalho()
        self._mostrar_status_agentes()
        
        # Entrada do tema
        tema = self._perguntar_tema()
        if not tema:
            return
        
        # Verificar modo Auto
        if tema.lower() == "auto":
            tema = self._gerar_tema_auto()
            self.console.print("\n[bold cyan]🤖 Modo AUTO - Code Review do sistema![/bold cyan]")
            self.console.print(Panel(
                "[green]📋 Os agentes vão analisar o código do sistema e sugerir melhorias.[/green]",
                title="Code Review Automática",
                border_style="cyan"
            ))
        
        self._mostrar_inicio_debate(tema)
        
        # Executar debate
        resultados = self._executar_debate(tema)
        
        # Mostrar resultados
        self._mostrar_resultados(resultados)
        
        # Modo interativo
        self._modo_interativo(tema)
    
    def _mostrar_cabecalho(self):
        """Mostra o cabeçalho do sistema."""
        self.console.print(Panel.fit(
            "[bold cyan]🎙️  4KINGS V2 - DEBATE ENGINE[/bold cyan]\n"
            "[dim]Arquitetura Enterprise com Circuit Breaker, Cache e Rate Limiting[/dim]\n"
            "[dim]Digite 'auto' para Code Review automática[/dim]",
            border_style="cyan"
        ))
    
    def _mostrar_status_agentes(self):
        """Mostra o status de todos os agentes disponíveis."""
        if not RICH_AVAILABLE:
            return
        
        table = Table(title="🤖 Agentes do Debate", box=box.ROUNDED)
        table.add_column("Agente", style="cyan", width=15)
        table.add_column("Modelo", style="green", width=30)
        table.add_column("Papel", style="yellow", width=25)
        table.add_column("Status", style="white", width=10)
        
        # Obter agentes do orquestrador
        agentes = getattr(self.orchestrator, 'agent_order', [])
        modelos = getattr(self.orchestrator, 'models', {})
        
        for agente in agentes:
            if agente in self.orchestrator.providers:
                status = "✅ Ativo"
                status_color = "green"
            else:
                status = "❌ Inativo"
                status_color = "red"
            
            modelo = modelos.get(agente, "N/A")
            papel = self._get_papel_agente(agente)
            
            table.add_row(
                f"{self.emoji.get(agente, '🤖')} {agente.capitalize()}",
                modelo[:25] + ("..." if len(modelo) > 25 else ""),
                papel[:22] + ("..." if len(papel) > 22 else ""),
                f"[{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
    
    def _get_papel_agente(self, agente: str) -> str:
        """Retorna o papel de um agente."""
        papeis = {
            'gemini': 'Especialista Teórico',
            'groq': 'Engenheiro Prático',
            'sambanova': 'Crítico Adversarial',
            'nvidia': 'Arquiteto de IA',
            'liquid': 'Especialista RAG',
            'thinking': 'Raciocínio Profundo',
            'cohere': 'Programador Agente',
            'zai': 'Planejador de Longo Prazo',
            'poolside': 'Engenheiro de Software',
            'curinga': 'Sintetizador',
        }
        return papeis.get(agente, 'Assistente')
    
    def _perguntar_tema(self) -> Optional[str]:
        """Pergunta o tema do debate."""
        if RICH_AVAILABLE:
            tema = Prompt.ask("\n[bold yellow]📝 Tema do debate (ou 'auto')[/bold yellow]")
        else:
            tema = input("\n📝 Tema do debate (ou 'auto'): ")
        return tema.strip() if tema else None
    
    def _mostrar_inicio_debate(self, tema: str):
        """Mostra mensagem de início do debate."""
        self.console.print(f"\n[green]▶ Iniciando debate sobre:[/green]")
        self.console.print(Panel(
            Markdown(tema[:200] + ("..." if len(tema) > 200 else "")),
            title="Tema",
            border_style="green"
        ))
        
        # Mostrar agentes ativos
        ativos = [a for a in self.orchestrator.providers.keys()]
        self.console.print(f"[dim]🤖 Agentes ativos: {', '.join(a.capitalize() for a in ativos)}[/dim]")
    
    def _executar_debate(self, tema: str) -> Dict:
        """
        Executa o debate completo.
        
        Returns:
            Dict com os resultados
        """
        resultados = {}
        
        # Quantas rodadas
        max_rounds = getattr(self.orchestrator, 'config', {}).get('debate', {}).get('max_rounds', 3)
        if isinstance(max_rounds, dict):
            max_rounds = max_rounds.get('max_rounds', 3)
        
        for rodada in range(1, max_rounds + 1):
            self.console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            self.console.print(f"[bold cyan]RODADA {rodada}[/bold cyan]")
            self.console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                transient=False,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Gerando respostas...", 
                    total=len(self.orchestrator.providers)
                )
                
                responses = self.orchestrator.run_round(tema, rodada)
                
                progress.update(task, completed=len(self.orchestrator.providers))
            
            # Exibir respostas
            for agente, resposta in responses.items():
                self._display_message(agente, resposta)
                time.sleep(0.5)
            
            resultados[rodada] = responses
        
        return resultados
    
    def _display_message(self, agente: str, message: str):
        """Exibe uma mensagem formatada."""
        if not RICH_AVAILABLE:
            print(f"\n💬 {agente.upper()}:")
            print(message)
            print("-"*40)
            return
        
        cor = self.cores.get(agente, 'white')
        emoji = self.emoji.get(agente, '🤖')
        nome = agente.capitalize()
        
        # Limitar tamanho da mensagem
        msg_display = message[:500] + ("..." if len(message) > 500 else "")
        
        self.console.print(f"\n[bold {cor}]{emoji} {nome}:[/bold {cor}]")
        self.console.print(Markdown(msg_display))
        self.console.print("-"*40, style="dim")
    
    def _mostrar_resultados(self, resultados: Dict):
        """Mostra os resultados finais do debate."""
        if not RICH_AVAILABLE:
            print("\n✅ Debate concluído!")
            return
        
        self.console.print("\n[bold green]✅ Debate concluído![/bold green]")
        
        # Resumo final
        summary = self.orchestrator.get_debate_summary()
        if summary:
            self.console.print(Panel(
                Markdown(summary[-500:]),
                title="📊 Resumo Final",
                border_style="green"
            ))
        
        # Métricas
        metrics = self.orchestrator.get_metrics()
        if metrics:
            self._mostrar_metricas(metrics)
    
    def _mostrar_metricas(self, metrics: Dict):
        """Mostra métricas do debate."""
        table = Table(title="📊 Métricas do Debate", box=box.ROUNDED)
        table.add_column("Provedor", style="cyan")
        table.add_column("Estado", style="white")
        table.add_column("Chamadas", style="white")
        table.add_column("Falhas", style="red")
        table.add_column("Cache", style="green")
        table.add_column("Rate Limit", style="yellow")
        
        for name, data in metrics.items():
            if name in ['gemini', 'groq', 'sambanova', 'nvidia', 'curinga']:
                health = data.get('health', {})
                cache = data.get('cache', {})
                rate = data.get('rate_limit', {})
                
                status_color = "green" if health.get('state') == 'CLOSED' else "red" if health.get('state') == 'OPEN' else "yellow"
                
                table.add_row(
                    name.capitalize(),
                    f"[{status_color}]{health.get('state', 'N/A')}[/{status_color}]",
                    str(health.get('total_calls', 0)),
                    str(health.get('failures', 0)),
                    f"{cache.get('hit_rate', 0):.1f}%",
                    f"{rate.get('usage_percent', 0):.1f}%"
                )
        
        self.console.print(table)
    
    def _modo_interativo(self, tema: str):
        """Modo interativo - usuário participa do debate."""
        self.console.print("\n[bold yellow]💬 Debate inicial concluído! Participe:[/bold yellow]")
        self.console.print("[dim]Digite sua mensagem ou 'sair' para encerrar[/dim]\n")
        
        try:
            while True:
                if RICH_AVAILABLE:
                    mensagem = Prompt.ask("[bold magenta]💭 Você[/bold magenta]")
                else:
                    mensagem = input("💭 Você: ").strip()
                
                if mensagem.lower() in ("sair", "exit", "quit"):
                    break
                
                if not mensagem.strip():
                    continue
                
                # Registrar fala do usuário
                if hasattr(self.orchestrator, 'state'):
                    self.orchestrator.state.add_fala("Você", mensagem)
                
                # Executar mais uma rodada
                self.console.print("\n[cyan]🔄 Continuando o debate...[/cyan]")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    task = progress.add_task("[cyan]Gerando respostas...", total=None)
                    responses = self.orchestrator.run_round(tema, 99)  # Rodada extra
                    progress.update(task, completed=True)
                
                for agente, resposta in responses.items():
                    self._display_message(agente, resposta)
                    time.sleep(0.5)
                
        except KeyboardInterrupt:
            self.console.print("\n\n[red]👋 Encerrado pelo usuário.[/red]")
    
    # ========================================================================
    # FUNÇÃO GERAR TEMA AUTO - CORRIGIDA
    # ========================================================================
    
    def _gerar_tema_auto(self) -> str:
        """
        Gera tema para Code Review automática com os arquivos REAIS do projeto.
        CORRIGIDO: Envia código resumido para o Groq para evitar erro 413.
        """
        try:
            codigo_completo = ""      # Para o Gemini (análise detalhada)
            codigo_resumido = ""      # Para o Groq (visão geral - evita 413)
            arquivos_encontrados = []
            
            # Lista de arquivos para revisar
            arquivos_para_revisar = [
                'main.py',
                'orchestrator_real.py',
                'debate_engine_ui.py',
            ]
            
            for arquivo in arquivos_para_revisar:
                if os.path.exists(arquivo):
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                        linhas = conteudo.split('\n')
                        
                        # ===== Código RESUMIDO para o Groq (50 linhas) =====
                        linhas_resumido = linhas[:50]
                        if len(linhas) > 50:
                            linhas_resumido.append(f"... [TRUNCADO - {len(linhas) - 50} linhas omitidas] ...")
                        
                        codigo_resumido += f"\n\n# ===== {arquivo} (RESUMIDO) =====\n"
                        codigo_resumido += '\n'.join(linhas_resumido)
                        
                        # ===== Código COMPLETO para o Gemini (200 linhas) =====
                        linhas_completo = linhas[:200]
                        if len(linhas) > 200:
                            linhas_completo.append(f"... [TRUNCADO - {len(linhas) - 200} linhas omitidas] ...")
                        
                        codigo_completo += f"\n\n# ===== {arquivo} =====\n"
                        codigo_completo += '\n'.join(linhas_completo)
                        
                        arquivos_encontrados.append(arquivo)
                        print(f"📄 Lido: {arquivo} ({len(linhas)} linhas)")
            
            if not arquivos_encontrados:
                with open(__file__, 'r', encoding='utf-8') as f:
                    conteudo = f.read()
                    linhas = conteudo.split('\n')
                    
                    linhas_resumido = linhas[:50]
                    if len(linhas) > 50:
                        linhas_resumido.append(f"... [TRUNCADO - {len(linhas) - 50} linhas] ...")
                    codigo_resumido = '\n'.join(linhas_resumido)
                    
                    linhas_completo = linhas[:200]
                    if len(linhas) > 200:
                        linhas_completo.append(f"... [TRUNCADO - {len(linhas) - 200} linhas] ...")
                    codigo_completo = '\n'.join(linhas_completo)
                    
                    arquivos_encontrados = [os.path.basename(__file__)]
            
            # ===== CONSTRUIR O TEMA =====
            tema = "# CODE REVIEW AUTOMÁTICA DO 4KINGS DEBATE ENGINE\n\n"
            tema += "## Contexto\n"
            tema += "Este é o código do 4KINGS Debate Engine V2 - um sistema multi-agente\n"
            tema += "que promove debates entre diferentes LLMs (Gemini, Groq, etc).\n\n"
            tema += "## Arquivos para Revisão (" + str(len(arquivos_encontrados)) + " arquivos):\n"
            tema += ", ".join(arquivos_encontrados) + "\n\n"
            
            # ===== SEÇÃO 1: Código RESUMIDO (para o Groq) =====
            tema += "## CÓDIGO RESUMIDO (para visão geral):\n\n"
            tema += "```python\n"
            tema += codigo_resumido
            tema += "\n```\n\n"
            
            # ===== SEÇÃO 2: Código COMPLETO (para o Gemini) =====
            tema += "## CÓDIGO COMPLETO (para análise detalhada):\n\n"
            tema += "```python\n"
            tema += codigo_completo
            tema += "\n```\n\n"
            
            # ===== ANÁLISE =====
            tema += "## O que analisar:\n\n"
            tema += "1. **Arquitetura**: Estrutura de classes, padrões de design, organização\n"
            tema += "2. **Tratamento de Erros**: Robustez, fallbacks, retry, circuit breakers\n"
            tema += "3. **Segurança**: Sanitização, mascaramento de chaves, validação de inputs\n"
            tema += "4. **Eficiência**: Uso de cache, chamadas assíncronas, otimização de tokens\n"
            tema += "5. **Manutenibilidade**: Type hints, docstrings, modularidade\n"
            tema += "6. **Melhorias**: Sugestões de novos recursos ou otimizações\n\n"
            tema += "Por favor, forneça sua análise detalhada baseada no código acima.\n"
            tema += "Seja específico, aponte trechos de código e sugira melhorias concretas.\n"
            tema += "Responda em Português do Brasil, de forma clara e objetiva."
            
            print(f"📊 Tema gerado com {len(codigo_completo)} caracteres de código")
            return tema
            
        except Exception as e:
            tema = "# CODE REVIEW AUTOMÁTICA DO 4KINGS DEBATE ENGINE\n\n"
            tema += "## Erro ao ler os arquivos\n\n"
            tema += "Não foi possível ler os arquivos do projeto para revisão.\n\n"
            tema += "Erro: " + str(e) + "\n\n"
            tema += "Por favor, forneça uma análise geral sobre como melhorar\n"
            tema += "a arquitetura de um sistema multi-agente de debates com LLMs.\n\n"
            tema += "Responda em Português do Brasil."
            return tema
    
    # ========================================================================
    # INTERFACE BÁSICA (Fallback)
    # ========================================================================
    
    def _run_basic(self):
        """Interface básica (fallback quando Rich não está disponível)."""
        print("\n" + "="*60)
        print("🎙️  4KINGS V2 - DEBATE ENGINE")
        print("="*60)
        print("\n💡 Digite 'auto' para Code Review\n")
        
        # Mostrar agentes
        print("🤖 Agentes disponíveis:")
        for nome in self.orchestrator.providers.keys():
            print(f"  ✅ {nome.capitalize()}")
        
        tema = input("\n📝 Tema do debate (ou 'auto'): ").strip()
        if not tema:
            print("❌ Tema não pode ser vazio!")
            return
        
        if tema.lower() == "auto":
            print("\n🤖 Modo AUTO - Code Review!")
            tema = self._gerar_tema_auto()
        
        print(f"\n🔄 Iniciando debate sobre: {tema[:100]}...\n")
        
        # Executar debate
        max_rounds = getattr(self.orchestrator, 'config', {}).get('debate', {}).get('max_rounds', 3)
        if isinstance(max_rounds, dict):
            max_rounds = max_rounds.get('max_rounds', 3)
        
        for rodada in range(1, max_rounds + 1):
            print(f"\n{'='*60}")
            print(f"RODADA {rodada}")
            print('='*60 + "\n")
            
            responses = self.orchestrator.run_round(tema, rodada)
            
            for agente, resposta in responses.items():
                print(f"\n💬 {agente.upper()}:")
                print(resposta[:500] + ("..." if len(resposta) > 500 else ""))
                print("-"*40)
                time.sleep(0.5)
        
        print("\n✅ Debate concluído!")
        
        # Modo interativo
        print("\n💬 Debate inicial concluído! Participe:")
        print("Digite sua mensagem ou 'sair' para encerrar\n")
        
        try:
            while True:
                mensagem = input("💭 Você: ").strip()
                if mensagem.lower() in ("sair", "exit", "quit"):
                    break
                if not mensagem:
                    continue
                
                if hasattr(self.orchestrator, 'state'):
                    self.orchestrator.state.add_fala("Você", mensagem)
                
                print("\n🔄 Continuando o debate...\n")
                
                responses = self.orchestrator.run_round(tema, 99)
                
                for agente, resposta in responses.items():
                    print(f"\n💬 {agente.upper()}:")
                    print(resposta[:500] + ("..." if len(resposta) > 500 else ""))
                    print("-"*40)
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            print("\n\n👋 Encerrado pelo usuário.")


# ==============================================================================
# FUNÇÃO AUXILIAR PARA TESTE
# ==============================================================================

def criar_ui(orchestrator):
    """
    Factory function para criar a UI.
    
    Args:
        orchestrator: Instância do DebateOrchestrator
    
    Returns:
        DebateUI: Instância da interface
    """
    return DebateUI(orchestrator)