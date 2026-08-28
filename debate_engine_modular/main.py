#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
main.py - 4KINGS Debate Engine com 6 Agentes
Gemini, Groq, Nemotron, Curinga, DeepSeek e NVIDIA NIM
"""

import os
import sys
import time
import random
from getpass import getpass
from typing import Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Importar módulos
from .interfaces import IApiProvider
from .providers.factory import ProviderFactory
from .providers.gemini import GeminiProvider
from .providers.groq import GroqProvider
from .providers.openrouter import OpenRouterProvider
from .providers.nvidia import NvidiaProvider
from .utils.clean_response import clean_response

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

INSTRUCAO_IDIOMA = "Responda SEMPRE em português do Brasil. Nunca responda em inglês."

PAPEIS = {
    'gemini': f"Especialista Teórico - Fundamente com frameworks, conceitos e teoria. {INSTRUCAO_IDIOMA}",
    'groq': f"Engenheiro Prático - Dê soluções concretas, exemplos práticos e código. {INSTRUCAO_IDIOMA}",
    'nemotron': f"Crítico Adversarial - Aponte falhas lógicas, contradições e pontos fracos. {INSTRUCAO_IDIOMA}",
    'curinga': f"Sintetizador - Una os argumentos, aponte convergências e divergências. {INSTRUCAO_IDIOMA}",
    'deepseek': f"Especialista em Raciocínio - Analise com profundidade lógica e matemática. {INSTRUCAO_IDIOMA}",
    'nvidia': f"Especialista em Performance - Foque em eficiência computacional, otimização e escalabilidade. {INSTRUCAO_IDIOMA}"
}

CORES = {
    'gemini': 'blue',
    'groq': 'green',
    'nemotron': 'orange1',
    'curinga': 'magenta',
    'deepseek': 'cyan',
    'nvidia': 'bright_green'
}

EMOJIS = {
    'gemini': '🔬',
    'groq': '⚡',
    'nemotron': '🔍',
    'curinga': '🔄',
    'deepseek': '🧠',
    'nvidia': '🚀'
}

PAPEIS_DISPLAY = {
    'gemini': 'Teórico',
    'groq': 'Prático',
    'nemotron': 'Crítico',
    'curinga': 'Sintetizador',
    'deepseek': 'Raciocínio',
    'nvidia': 'Performance'
}

# ==============================================================================
# PROMPT BUILDER
# ==============================================================================

class PromptBuilder:
    def build_prompt(self, tema: str, resumo: str, falas: List[tuple], agente: str, max_historico: int = 3) -> str:
        falas_recentes = falas[-max_historico:] if falas else []
        falas_txt = "\n".join(f"[{n}]: {t[:200]}" for n, t in falas_recentes) if falas_recentes else "Nenhuma contribuição ainda."
        papel = PAPEIS.get(agente, f"Você é um assistente. {INSTRUCAO_IDIOMA}")
        return f"""{papel}

Tema: {tema}

Resumo Atual:
{resumo or "Início do debate."}

Últimas Contribuições:
{falas_txt}

Sua Resposta (máximo 300 palavras, seja direto e objetivo):"""

# ==============================================================================
# DEBATE ENGINE (COM 6 AGENTES)
# ==============================================================================

class DebateEngine:
    def __init__(self, providers: Dict[str, IApiProvider]):
        self.providers = providers
        self.prompt_builder = PromptBuilder()
        self.historico = ""
        self.resumo = ""
        self.falas: List[tuple] = []
        self.todas_falas: List[tuple] = []
        self.console = Console() if RICH_AVAILABLE else None
        
        # Mapeamento de agentes para providers
        self.agente_para_provider = {
            'gemini': 'gemini',
            'groq': 'groq',
            'nemotron': 'openrouter',
            'curinga': 'openrouter',
            'deepseek': 'openrouter',
            'nvidia': 'nvidia'
        }
        
        # Agentes ativos
        self.agentes_ativos = []
        if 'gemini' in self.providers:
            self.agentes_ativos.append('gemini')
        if 'groq' in self.providers:
            self.agentes_ativos.append('groq')
        if 'openrouter' in self.providers:
            self.agentes_ativos.append('nemotron')
            self.agentes_ativos.append('curinga')
            self.agentes_ativos.append('deepseek')
        if 'nvidia' in self.providers:
            self.agentes_ativos.append('nvidia')
        
        print(f"🤖 Agentes ativos: {', '.join(self.agentes_ativos)}")
    
    def run_round(self, tema: str, round_num: int) -> Dict[str, str]:
        if not self.agentes_ativos:
            return {"Erro": "Nenhum agente disponível"}
        
        print(f"\n{'='*60}")
        print(f"RODADA {round_num}")
        print('='*60)
        
        ordem = self.agentes_ativos.copy()
        random.shuffle(ordem)
        
        respostas = {}
        
        for agente in ordem:
            provider_nome = self.agente_para_provider.get(agente)
            provider = self.providers.get(provider_nome)
            
            if not provider:
                print(f"⚠️ Provedor para {agente} não encontrado")
                continue
            
            papel = PAPEIS.get(agente, f"Você é um assistente. {INSTRUCAO_IDIOMA}")
            prompt = self.prompt_builder.build_prompt(tema, self.resumo, self.falas, agente)
            
            cor = CORES.get(agente, 'white')
            emoji = EMOJIS.get(agente, '🤖')
            
            if RICH_AVAILABLE and self.console:
                self.console.print(f"\n[bold {cor}]{emoji} {agente.capitalize()} pensando...[/bold {cor}]")
            else:
                print(f"\n{emoji} {agente.capitalize()} pensando...")
            
            resposta = provider.call(prompt, papel, max_tokens=800, temperature=0.3)
            
            if not resposta.startswith("[Erro") and not resposta.startswith("[Circuit Breaker"):
                self.falas.append((agente, resposta))
                self.todas_falas.append((agente, resposta))
                self.historico += f"\n[{agente}]: {resposta}\n"
                respostas[agente] = resposta
                
                cor = CORES.get(agente, 'white')
                emoji = EMOJIS.get(agente, '🤖')
                nome = agente.capitalize()
                resp_display = resposta[:500] + ("..." if len(resposta) > 500 else "")
                
                if RICH_AVAILABLE and self.console:
                    self.console.print(f"\n[bold {cor}]{emoji} {nome}:[/bold {cor}]")
                    self.console.print(Markdown(resp_display))
                else:
                    print(f"\n{emoji} {nome}:")
                    print(resp_display)
                print("-"*40)
            else:
                print(f"\n⚠️ {agente.capitalize()} falhou: {resposta[:100]}")
            
            time.sleep(2)
        
        self.resumo = self._gerar_resumo()
        self.falas = []
        
        return respostas
    
    def _gerar_resumo(self) -> str:
        if not self.todas_falas:
            return self.resumo
        ultimas = self.todas_falas[-6:]
        resumo = "Pontos principais: " + "; ".join([
            f"{nome}: {texto[:80]}..." for nome, texto in ultimas
        ])
        return resumo[:300]
    
    def get_debate_summary(self) -> str:
        return self.historico

# ==============================================================================
# UI
# ==============================================================================

class DebateUI:
    def __init__(self, engine: DebateEngine):
        self.engine = engine
        self.console = Console() if RICH_AVAILABLE else None
    
    def run(self):
        if RICH_AVAILABLE:
            self._run_rich()
        else:
            self._run_basic()
    
    def _run_rich(self):
        self.console.print(Panel.fit(
            "[bold cyan]🎙️  4KINGS V2 - DEBATE ENGINE[/bold cyan]\n"
            "[dim]6 Agentes: Gemini, Groq, Nemotron, Curinga, DeepSeek, NVIDIA NIM[/dim]",
            border_style="cyan"
        ))
        
        table = Table(title="🤖 Agentes do Debate", box=box.ROUNDED)
        table.add_column("Agente", style="cyan")
        table.add_column("Papel", style="yellow")
        table.add_column("Modelo", style="green")
        table.add_column("Status", style="white")
        
        for agente in self.engine.agentes_ativos:
            papel = PAPEIS_DISPLAY.get(agente, "N/A")
            emoji = EMOJIS.get(agente, '🤖')
            provider_nome = self.engine.agente_para_provider.get(agente)
            provider = self.engine.providers.get(provider_nome)
            modelo = provider.get_modelo_atual() if provider else "N/A"
            
            table.add_row(
                f"{emoji} {agente.capitalize()}",
                papel,
                modelo[:30] + ("..." if len(modelo) > 30 else ""),
                "✅ Ativo"
            )
        
        self.console.print(table)
        
        tema = self.console.input("\n[bold yellow]📝 Tema do debate (ou 'auto'): [/bold yellow]")
        if not tema.strip():
            self.console.print("[red]❌ Tema não pode ser vazio![/red]")
            return
        
        if tema.lower() == "auto":
            tema = self._gerar_tema_auto()
            self.console.print("\n[bold cyan]🤖 Modo AUTO - Code Review![/bold cyan]")
        
        self.console.print("\n[green]▶ Iniciando debate...[/green]")
        
        for rodada in range(1, 4):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task(f"Rodada {rodada}...", total=None)
                self.engine.run_round(tema, rodada)
                progress.update(task, completed=True)
        
        self._show_results()
    
    def _gerar_tema_auto(self) -> str:
        try:
            with open(__file__, 'r', encoding='utf-8') as f:
                codigo = f.read()
            
            linhas = codigo.split('\n')
            codigo_resumido = '\n'.join(linhas[:200])
            
            if len(linhas) > 200:
                codigo_resumido += f"\n\n... [CÓDIGO TRUNCADO - {len(linhas) - 200} linhas omitidas] ...\n"
            
            tema = "# CODE REVIEW AUTOMÁTICA DO 4KINGS DEBATE ENGINE\n\n"
            tema += "## Contexto\n"
            tema += "Este é o código do 4KINGS Debate Engine V2.\n\n"
            tema += "## Código para Revisão:\n\n```python\n"
            tema += codigo_resumido
            tema += "\n```\n\n"
            tema += "## O que analisar:\n\n"
            tema += "1. **Arquitetura**: Strategy Pattern, injeção de dependência\n"
            tema += "2. **Tratamento de Erros**: Circuit Breaker, Rate Limiter, Cache\n"
            tema += "3. **Segurança**: Sanitização, mascaramento de chaves\n"
            tema += "4. **Eficiência**: Cache, chamadas assíncronas, otimização\n"
            tema += "5. **Manutenibilidade**: Type hints, docstrings, modularidade\n\n"
            tema += "Responda em Português do Brasil, de forma clara e objetiva."
            
            return tema
        except Exception as e:
            return f"Code Review do sistema (erro ao ler código: {e})"
    
    def _show_results(self):
        self.console.print("\n[bold green]✅ Debate concluído![/bold green]")
        
        historico = self.engine.get_debate_summary()
        if historico:
            self.console.print(Panel(
                Markdown(historico[-500:]),
                title="📊 Resumo Final",
                border_style="green"
            ))
    
    def _run_basic(self):
        print("\n" + "="*60)
        print("🎙️  4KINGS V2 - DEBATE ENGINE")
        print("="*60)
        
        print("\n🤖 Agentes disponíveis:")
        for agente in self.engine.agentes_ativos:
            emoji = EMOJIS.get(agente, '🤖')
            print(f"  {emoji} {agente.capitalize()}")
        
        tema = input("\n📝 Tema do debate (ou 'auto'): ").strip()
        if not tema:
            print("❌ Tema não pode ser vazio!")
            return
        
        if tema.lower() == "auto":
            print("\n🤖 Modo AUTO - Code Review!")
            tema = self._gerar_tema_auto()
        
        print("\n🔄 Iniciando debate...")
        
        for rodada in range(1, 4):
            self.engine.run_round(tema, rodada)
        
        print("\n✅ Debate concluído!")

# ==============================================================================
# FACTORY DE PROVEDORES
# ==============================================================================

class ProviderFactory:
    def create_providers(self, gemini_key=None, groq_key=None, openrouter_key=None, nvidia_key=None) -> Dict[str, IApiProvider]:
        providers = {}
        
        if gemini_key:
            try:
                providers['gemini'] = GeminiProvider(gemini_key)
            except Exception as e:
                print(f"⚠️ Gemini: {e}")
        
        if groq_key:
            try:
                providers['groq'] = GroqProvider(groq_key)
            except Exception as e:
                print(f"⚠️ Groq: {e}")
        
        if openrouter_key:
            try:
                providers['openrouter'] = OpenRouterProvider(openrouter_key)
            except Exception as e:
                print(f"⚠️ OpenRouter: {e}")
        
        if nvidia_key:
            try:
                providers['nvidia'] = NvidiaProvider(nvidia_key)
            except Exception as e:
                print(f"⚠️ NVIDIA NIM: {e}")
        
        return providers

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n🚀 Iniciando 4KINGS Debate Engine (6 Agentes)...\n")
    print("📌 AGENTES:")
    print("   🔬 Gemini (Teórico) - SDK Nativo")
    print("   ⚡ Groq (Prático) - API Groq")
    print("   🔍 Nemotron (Crítico) - via OpenRouter")
    print("   🧠 DeepSeek (Raciocínio) - via OpenRouter")
    print("   🚀 NVIDIA NIM (Performance) - via NVIDIA NIM")
    print("   🔄 Curinga (Sintetizador) - via OpenRouter\n")
    
    # Carregar chaves
    keys = {
        'gemini': os.environ.get('GEMINI_API_KEY'),
        'groq': os.environ.get('GROQ_API_KEY'),
        'openrouter': os.environ.get('OPENROUTER_API_KEY'),
        'nvidia': os.environ.get('NVIDIA_API_KEY'),
    }
    
    for provider, key in keys.items():
        if not key:
            keys[provider] = getpass(f"Chave da API {provider.capitalize()}: ").strip()
    
    # Criar provedores
    factory = ProviderFactory()
    providers = factory.create_providers(
        gemini_key=keys['gemini'],
        groq_key=keys['groq'],
        openrouter_key=keys['openrouter'],
        nvidia_key=keys['nvidia']
    )
    
    if not providers:
        print("\n❌ Nenhuma API configurada!")
        print("\nCrie um arquivo .env com:")
        print("GEMINI_API_KEY=sua_chave")
        print("GROQ_API_KEY=sua_chave")
        print("OPENROUTER_API_KEY=sua_chave")
        print("NVIDIA_API_KEY=sua_chave")
        sys.exit(1)
    
    engine = DebateEngine(providers)
    ui = DebateUI(engine)
    
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\n\n👋 Encerrado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()