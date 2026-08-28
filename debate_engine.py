#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
4KINGS DEBATE ENGINE V3 (SEM CLAUDE)
- Agentes: Gemini, Groq, Mistral, Ollama, OpenAI
- Moderador automático (síntese entre rodadas)
- Suporte a CLI (argparse), logs, persistência e configuração modular
"""

import os
import sys
import time
import re
import random
import json
import argparse
import logging
import subprocess
from datetime import datetime
from getpass import getpass
from typing import Optional, Dict, List, Tuple
from collections import deque

# ==============================================================================
# 0. CONFIGURAÇÃO DE TERMINAL (UTF-8)
# ==============================================================================
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stdin, sys.stderr):
        try:
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

# ==============================================================================
# 1. IMPORTAÇÕES
# ==============================================================================
try:
    from google import genai
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"⚠️ Erro ao importar dependências: {e}")
    print("Instale: pip install google-generativeai openai python-dotenv")
    sys.exit(1)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ Requests não instalado. Instale: pip install requests")

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

# ==============================================================================
# 2. CONFIGURAÇÃO – AGENTES E PAPÉIS
# ==============================================================================

INSTRUCAO_IDIOMA = "Responda SEMPRE em português do Brasil. Nunca responda em inglês."

# Definições dos agentes (nome -> papel, cor, emoji, display)
AGENT_CONFIG = {
    'gemini': {
        'papel': f"Especialista Teórico - Fundamente com frameworks, conceitos e teoria. {INSTRUCAO_IDIOMA}",
        'cor': 'blue',
        'emoji': '🔬',
        'display': 'Teórico',
        'provider': 'gemini',
        'modelo_padrao': 'gemini-3.6-flash',
        'parametros': {'max_tokens': 800, 'temperature': 0.3, 'rpm': 5}
    },
    'groq': {
        'papel': f"Engenheiro Prático - Dê soluções concretas, exemplos práticos e código. {INSTRUCAO_IDIOMA}",
        'cor': 'green',
        'emoji': '⚡',
        'display': 'Prático',
        'provider': 'groq',
        'modelo_padrao': 'openai/gpt-oss-120b',
        'parametros': {'max_tokens': 1000, 'temperature': 0.3, 'rpm': 8}
    },
    'mistral': {
        'papel': f"Especialista em Raciocínio Lógico - Análise profunda e estruturada. {INSTRUCAO_IDIOMA}",
        'cor': 'yellow',
        'emoji': '🧩',
        'display': 'Lógico',
        'provider': 'mistral',
        'modelo_padrao': 'mistral-small-latest',
        'parametros': {'max_tokens': 600, 'temperature': 0.2, 'rpm': 30}
    },
    'ollama': {
        'papel': f"Especialista Local - Modelo executado localmente, sem custos e com privacidade total. {INSTRUCAO_IDIOMA}",
        'cor': 'magenta',
        'emoji': '🦙',
        'display': 'Local',
        'provider': 'ollama',
        'modelo_padrao': 'llama3.2:latest',
        'parametros': {'max_tokens': 800, 'temperature': 0.3, 'rpm': 999}
    },
    'openai': {
        'papel': f"Especialista em IA Generativa - Visão pragmática e moderna. {INSTRUCAO_IDIOMA}",
        'cor': 'cyan',
        'emoji': '🤖',
        'display': 'OpenAI',
        'provider': 'openai',
        'modelo_padrao': 'gpt-4o-mini',
        'parametros': {'max_tokens': 800, 'temperature': 0.3, 'rpm': 10}
    }
}

# Fallbacks de modelos por provedor (usados se o principal falhar)
FALLBACK_MODELS = {
    'gemini': ['gemini-3.5-flash', 'gemini-2.5-flash'],
    'groq': ['openai/gpt-oss-20b', 'qwen/qwen3.6-27b'],
    'mistral': ['mistral-tiny-latest', 'openrouter/free'],
    'ollama': ['llama3.2:latest', 'mistral:latest', 'phi3:latest'],
    'openai': ['gpt-4o-mini', 'gpt-3.5-turbo']
}

# ==============================================================================
# 3. DETECÇÃO AUTOMÁTICA DE MODELOS
# ==============================================================================

def detectar_modelos_groq(api_key: str) -> List[str]:
    """Detecta modelos disponíveis no Groq"""
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        modelos = client.models.list()
        disponiveis = [m.id for m in modelos.data]
        chat_models = [m for m in disponiveis 
                      if not any(x in m.lower() for x in ['whisper', 'embed', 'guard', 'tts'])]
        prioridades = [
            'openai/gpt-oss-120b',
            'openai/gpt-oss-20b',
            'qwen/qwen3.6-27b'
        ]
        resultado = []
        for p in prioridades:
            if p in chat_models and p not in resultado:
                resultado.append(p)
        for m in chat_models:
            if m not in resultado:
                resultado.append(m)
        resultado = [m for m in resultado if 'compound' not in m.lower()]
        return resultado
    except Exception as e:
        logging.error(f"Groq model detection failed: {e}")
        return FALLBACK_MODELS['groq']

def detectar_modelos_gemini(api_key: str) -> List[str]:
    """Detecta modelos disponíveis no Gemini"""
    try:
        client = genai.Client(api_key=api_key)
        modelos = client.models.list()
        nomes = []
        for m in modelos:
            if hasattr(m, 'name'):
                nome = m.name
                if 'gemini' in nome.lower():
                    if nome.startswith('models/'):
                        nome = nome[7:]
                    nomes.append(nome)
        prioridades = [
            'gemini-3.7-flash',
            'gemini-3.6-flash',
            'gemini-3.5-flash',
            'gemini-2.5-flash'
        ]
        resultado = []
        for p in prioridades:
            if p in nomes and p not in resultado:
                resultado.append(p)
        for m in nomes:
            if m not in resultado:
                resultado.append(m)
        return resultado
    except Exception as e:
        logging.error(f"Gemini model detection failed: {e}")
        return FALLBACK_MODELS['gemini']

def detectar_modelos_openai(api_key: str) -> List[str]:
    """Detecta modelos disponíveis na OpenAI"""
    try:
        client = OpenAI(api_key=api_key)
        modelos = client.models.list()
        nomes = [m.id for m in modelos.data]
        prioridades = [
            'gpt-4o-mini',
            'gpt-4o',
            'gpt-3.5-turbo'
        ]
        resultado = []
        for p in prioridades:
            if p in nomes and p not in resultado:
                resultado.append(p)
        for m in nomes:
            if m not in resultado:
                resultado.append(m)
        return resultado
    except Exception as e:
        logging.error(f"OpenAI model detection failed: {e}")
        return FALLBACK_MODELS['openai']

def detectar_ollama() -> Tuple[bool, List[str]]:
    """Detecta se o Ollama está rodando e quais modelos estão disponíveis"""
    if not REQUESTS_AVAILABLE:
        return False, []
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            modelos = [m['name'] for m in data.get('models', [])]
            if modelos:
                print(f"✅ Ollama detectado - modelos: {', '.join(modelos[:3])}...")
                return True, modelos
            else:
                print("⚠️ Ollama está rodando mas nenhum modelo encontrado")
                return True, []
        else:
            print("⚠️ Ollama não está rodando (localhost:11434)")
            return False, []
    except requests.exceptions.ConnectionError:
        print("⚠️ Ollama não está rodando (localhost:11434)")
        return False, []
    except Exception as e:
        print(f"⚠️ Erro ao detectar Ollama: {e}")
        return False, []

# ==============================================================================
# 4. CLASSES DE SUPORTE (Rate Limiter, Circuit Breaker, Cache)
# ==============================================================================

class RateLimiter:
    def __init__(self, max_calls_per_minute=8):
        self.max_calls = max_calls_per_minute
        self.calls = deque()
    def wait(self):
        now = time.time()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            sleep_time = 60 - (now - self.calls[0]) + 1
            print(f"⏳ Aguardando {sleep_time:.1f}s (rate limit)...")
            time.sleep(sleep_time)
        self.calls.append(time.time())

class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=120):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"
    def can_execute(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True
    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"
    def record_failure(self):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            self.last_failure_time = time.time()

class ResponseCache:
    def __init__(self, max_size=50, ttl_seconds=180):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = {}
        self.hits = 0
        self.misses = 0
    def get(self, key):
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                self.hits += 1
                return entry['response']
        self.misses += 1
        return None
    def set(self, key, response):
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1]['timestamp'])
            del self.cache[oldest[0]]
        self.cache[key] = {'response': response, 'timestamp': time.time()}
    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0

# ==============================================================================
# 5. LIMPEZA DE RESPOSTA
# ==============================================================================

def clean_response(text: str) -> str:
    """Limpa tags <think> e espaços extras"""
    if not text:
        return text
    while '<think>' in text and '</think>' in text:
        start = text.find('<think>')
        end = text.find('</think>') + 8
        text = text[:start] + text[end:]
    text = text.replace('User Safety: [', '').replace(']', '')
    text = text.replace('Safety: [', '').replace(']', '')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    return text.strip()

# ==============================================================================
# 6. FUNÇÕES DE CHAMADA PARA CADA PROVEDOR
# ==============================================================================

def call_gemini(client, prompt, papel, modelos, max_tokens=800, temperature=0.3, timeout=30):
    rate_limiter = RateLimiter(max_calls_per_minute=5)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: Gemini indisponível]"
    for modelo in modelos:
        try:
            print(f"🔄 Tentando Gemini: {modelo}")
            response = client.models.generate_content(
                model=modelo,
                contents=f"{papel}\n\n{prompt}"
            )
            if response.text and len(response.text) > 30:
                cb.record_success()
                return clean_response(response.text)
        except Exception as e:
            print(f"⚠️ Gemini ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                time.sleep(10)
            continue
    cb.record_failure()
    return "[Erro Gemini: Todos os modelos falharam]"

def call_groq(client, prompt, papel, modelos, max_tokens=1000, temperature=0.3, timeout=30):
    rate_limiter = RateLimiter(max_calls_per_minute=8)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: Groq indisponível]"
    for modelo in modelos:
        try:
            print(f"🔄 Tentando Groq: {modelo}")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            content = response.choices[0].message.content
            if content and len(content) > 20:
                cb.record_success()
                return clean_response(content)
        except Exception as e:
            print(f"⚠️ Groq ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                time.sleep(10)
            continue
    cb.record_failure()
    return "[Erro Groq: Todos os modelos falharam]"

def call_mistral(client, prompt, papel, modelos, max_tokens=600, temperature=0.2, timeout=30):
    rate_limiter = RateLimiter(max_calls_per_minute=30)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: Mistral indisponível]"
    for modelo in modelos:
        try:
            print(f"🔄 Tentando Mistral: {modelo}")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            content = response.choices[0].message.content
            if content and len(content) > 20:
                cb.record_success()
                return clean_response(content)
        except Exception as e:
            print(f"⚠️ Mistral ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                time.sleep(10)
            continue
    cb.record_failure()
    return "[Erro Mistral: Todos os modelos falharam]"

def call_ollama(client_info, prompt, papel, modelos, max_tokens=800, temperature=0.3, timeout=60):
    if not REQUESTS_AVAILABLE:
        return "[Erro: requests não instalado]"
    rate_limiter = RateLimiter(max_calls_per_minute=999)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: Ollama indisponível]"
    modelos_tentar = [client_info['modelo']] + modelos
    for modelo in modelos_tentar:
        try:
            print(f"🔄 Tentando Ollama: {modelo}")
            payload = {
                "model": modelo,
                "prompt": f"{papel}\n\n{prompt}",
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            response = requests.post(client_info['url'], json=payload, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                content = data.get('response', '')
                if content and len(content) > 20:
                    cb.record_success()
                    return clean_response(content)
            else:
                print(f"⚠️ Ollama ({modelo}): HTTP {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"⚠️ Ollama ({modelo}): timeout")
            continue
        except Exception as e:
            print(f"⚠️ Ollama ({modelo}): {str(e)[:60]}")
            continue
    cb.record_failure()
    return "[Erro Ollama: Todos os modelos falharam]"

def call_openai(client, prompt, papel, modelos, max_tokens=800, temperature=0.3, timeout=30):
    rate_limiter = RateLimiter(max_calls_per_minute=10)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: OpenAI indisponível]"
    for modelo in modelos:
        try:
            print(f"🔄 Tentando OpenAI: {modelo}")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            content = response.choices[0].message.content
            if content and len(content) > 20:
                cb.record_success()
                return clean_response(content)
        except Exception as e:
            print(f"⚠️ OpenAI ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                time.sleep(10)
            continue
    cb.record_failure()
    return "[Erro OpenAI: Todos os modelos falharam]"

# ==============================================================================
# 7. BUILDER DE PROMPT
# ==============================================================================

class PromptBuilder:
    def build_prompt(self, tema, resumo, falas, agente, max_historico=3):
        falas_recentes = falas[-max_historico:] if falas else []
        falas_txt = "\n".join(f"[{n}]: {t[:200]}" for n, t in falas_recentes) if falas_recentes else "Nenhuma contribuição ainda."
        papel = AGENT_CONFIG[agente]['papel']
        return f"""{papel}

Tema: {tema}

Resumo Atual:
{resumo or "Início do debate."}

Últimas Contribuições:
{falas_txt}

Sua Resposta (seja direto e objetivo):"""

# ==============================================================================
# 8. MOTOR DO DEBATE
# ==============================================================================

class DebateEngine:
    def __init__(self, clients, modelos, agentes_escolhidos=None, num_rodadas=3):
        self.clients = clients
        self.modelos = modelos
        self.prompt_builder = PromptBuilder()
        self.historico = ""
        self.resumo = ""
        self.falas = []
        self.todas_falas = []
        self.num_rodadas = num_rodadas
        self.console = Console() if RICH_AVAILABLE else None

        # Definir agentes ativos
        self.agentes_ativos = []
        if agentes_escolhidos:
            # Se o usuário passou uma lista, filtra pelos disponíveis
            for ag in agentes_escolhidos:
                if ag in AGENT_CONFIG and ag in self.clients:
                    self.agentes_ativos.append(ag)
                else:
                    print(f"⚠️ Agente {ag} não disponível ou não configurado.")
        else:
            # Usa todos os disponíveis
            for ag in AGENT_CONFIG:
                if ag in self.clients:
                    self.agentes_ativos.append(ag)

        # Adicionar sempre o moderador (não é um provedor)
        if 'moderador' not in self.agentes_ativos:
            self.agentes_ativos.append('moderador')

        # Modelos por agente (detectados ou padrão)
        self.modelos_agente = {}
        for ag in self.agentes_ativos:
            if ag == 'moderador':
                continue
            provider = AGENT_CONFIG[ag]['provider']
            if provider in self.modelos:
                self.modelos_agente[ag] = self.modelos[provider]
            else:
                self.modelos_agente[ag] = FALLBACK_MODELS.get(provider, [AGENT_CONFIG[ag]['modelo_padrao']])

        print(f"🤖 Agentes ativos: {', '.join(self.agentes_ativos)}")

    def run_round(self, tema, round_num):
        print(f"\n{'='*60}\nRODADA {round_num}\n{'='*60}")
        ordem = [ag for ag in self.agentes_ativos if ag != 'moderador']
        random.shuffle(ordem)
        respostas = {}

        for agente in ordem:
            provider = AGENT_CONFIG[agente]['provider']
            client = self.clients.get(provider)
            if not client:
                print(f"⚠️ Cliente para {agente} não encontrado")
                continue

            papel = AGENT_CONFIG[agente]['papel']
            prompt = self.prompt_builder.build_prompt(tema, self.resumo, self.falas, agente)
            modelos = self.modelos_agente.get(agente, [])
            params = AGENT_CONFIG[agente]['parametros']
            max_tokens = params['max_tokens']
            temperature = params['temperature']

            cor = AGENT_CONFIG[agente]['cor']
            emoji = AGENT_CONFIG[agente]['emoji']

            if RICH_AVAILABLE and self.console:
                self.console.print(f"\n[bold {cor}]{emoji} {agente.capitalize()} pensando...[/bold {cor}]")
            else:
                print(f"\n{emoji} {agente.capitalize()} pensando...")

            # Chamada específica do provedor
            if provider == 'gemini':
                resposta = call_gemini(client, prompt, papel, modelos, max_tokens, temperature)
            elif provider == 'groq':
                resposta = call_groq(client, prompt, papel, modelos, max_tokens, temperature)
            elif provider == 'mistral':
                resposta = call_mistral(client, prompt, papel, modelos, max_tokens, temperature)
            elif provider == 'ollama':
                resposta = call_ollama(client, prompt, papel, modelos, max_tokens, temperature)
            elif provider == 'openai':
                resposta = call_openai(client, prompt, papel, modelos, max_tokens, temperature)
            else:
                continue

            if not resposta.startswith("[Erro") and not resposta.startswith("[Circuit Breaker"):
                self.falas.append((agente, resposta))
                self.todas_falas.append((agente, resposta))
                self.historico += f"\n[{agente}]: {resposta}\n"
                respostas[agente] = resposta

                resp_display = resposta[:500] + ("..." if len(resposta) > 500 else "")
                if RICH_AVAILABLE and self.console:
                    self.console.print(f"\n[bold {cor}]{emoji} {agente.capitalize()}:[/bold {cor}]")
                    self.console.print(Markdown(resp_display))
                else:
                    print(f"\n{emoji} {agente.capitalize()}:")
                    print(resp_display)
                print("-"*40)
            else:
                print(f"\n⚠️ {agente.capitalize()} falhou: {resposta[:100]}")

            time.sleep(2)

        # Moderador: resumo da rodada
        if 'moderador' in self.agentes_ativos:
            self._gerar_resumo_moderador(tema)

        self.falas = []

    def _gerar_resumo_moderador(self, tema):
        """Gera um resumo sintético do debate até agora"""
        if not self.todas_falas:
            return
        # Pega as últimas 5 falas
        ultimas = self.todas_falas[-5:]
        texto = "Síntese do moderador:\n"
        for nome, resp in ultimas:
            texto += f"- {nome}: {resp[:100]}...\n"
        texto += "\nPontos em comum: ...\nPontos divergentes: ..."
        # Salva no histórico
        self.historico += f"\n[moderador]: {texto}\n"
        self.resumo = texto
        if RICH_AVAILABLE and self.console:
            self.console.print(f"\n[bold red]🧠 Moderador:[/bold red]")
            self.console.print(Markdown(texto))
        else:
            print(f"\n🧠 Moderador:")
            print(texto)

    def get_historico(self):
        return self.historico

# ==============================================================================
# 9. INTERFACE DE USUÁRIO (RICH ou BÁSICA)
# ==============================================================================

class DebateUI:
    def __init__(self, engine, output_file=None):
        self.engine = engine
        self.output_file = output_file
        self.console = Console() if RICH_AVAILABLE else None

    def run(self, tema=None, rodadas=None):
        if RICH_AVAILABLE:
            self._run_rich(tema, rodadas)
        else:
            self._run_basic(tema, rodadas)

    def _run_rich(self, tema, rodadas):
        self.console.print(Panel.fit(
            "[bold cyan]🎙️  4KINGS DEBATE ENGINE V3[/bold cyan]\n"
            "[dim]Agentes: Gemini, Groq, Mistral, Ollama, OpenAI, Moderador[/dim]",
            border_style="cyan"
        ))

        table = Table(title="🤖 Agentes do Debate", box=box.ROUNDED)
        table.add_column("Agente", style="cyan")
        table.add_column("Papel", style="yellow")
        table.add_column("Modelo", style="green")
        table.add_column("Tokens", style="white")
        table.add_column("Status", style="white")

        for agente in self.engine.agentes_ativos:
            if agente == 'moderador':
                table.add_row("🧠 Moderador", "Síntese", "-", "-", "✅ Ativo")
                continue
            papel = AGENT_CONFIG[agente]['display']
            emoji = AGENT_CONFIG[agente]['emoji']
            modelo = self.engine.modelos_agente.get(agente, ['N/A'])[0]
            params = AGENT_CONFIG[agente]['parametros']
            tokens = params['max_tokens']
            table.add_row(f"{emoji} {agente.capitalize()}", papel, modelo[:25] + ("..." if len(modelo) > 25 else ""), str(tokens), "✅ Ativo")

        self.console.print(table)

        if not tema:
            tema = self.console.input("\n[bold yellow]📝 Tema do debate (ou 'auto'): [/bold yellow]")
            if not tema.strip():
                self.console.print("[red]❌ Tema não pode ser vazio![/red]")
                return
            if tema.lower() == "auto":
                tema = self._gerar_tema_auto()
                self.console.print("\n[bold cyan]🤖 Modo AUTO - Code Review![/bold cyan]")

        rodadas = rodadas or self.engine.num_rodadas
        self.console.print(f"\n[green]▶ Iniciando debate com {rodadas} rodada(s)...[/green]")

        for r in range(1, rodadas+1):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task(f"Rodada {r}...", total=None)
                self.engine.run_round(tema, r)
                progress.update(task, completed=True)

        self._show_results()

    def _run_basic(self, tema, rodadas):
        print("\n" + "="*60)
        print("🎙️  4KINGS DEBATE ENGINE V3")
        print("="*60)
        print("\n🤖 Agentes disponíveis:")
        for agente in self.engine.agentes_ativos:
            if agente == 'moderador':
                print("  🧠 Moderador (síntese)")
            else:
                emoji = AGENT_CONFIG[agente]['emoji']
                print(f"  {emoji} {agente.capitalize()}")

        if not tema:
            tema = input("\n📝 Tema do debate (ou 'auto'): ").strip()
            if not tema:
                print("❌ Tema não pode ser vazio!")
                return
            if tema.lower() == "auto":
                print("\n🤖 Modo AUTO - Code Review!")
                tema = self._gerar_tema_auto()

        rodadas = rodadas or self.engine.num_rodadas
        print(f"\n🔄 Iniciando debate com {rodadas} rodada(s)...")

        for r in range(1, rodadas+1):
            self.engine.run_round(tema, r)

        self._show_results()

    def _gerar_tema_auto(self) -> str:
        try:
            with open(__file__, 'r', encoding='utf-8') as f:
                codigo = f.read()
            linhas = codigo.split('\n')
            codigo_resumido = '\n'.join(linhas[:200])
            if len(linhas) > 200:
                codigo_resumido += f"\n\n... [CÓDIGO TRUNCADO - {len(linhas) - 200} linhas omitidas] ...\n"
            tema = "# CODE REVIEW AUTOMÁTICA DO DEBATE ENGINE\n\n"
            tema += "## Contexto\nEste é o código do Debate Engine V3.\n\n"
            tema += "## Código para Revisão:\n\n```python\n"
            tema += codigo_resumido
            tema += "\n```\n\n"
            tema += "## O que analisar:\n\n"
            tema += "1. **Arquitetura**: Estrutura de classes, padrões de design\n"
            tema += "2. **Tratamento de Erros**: Robustez, fallbacks\n"
            tema += "3. **Segurança**: Sanitização, mascaramento de chaves\n"
            tema += "4. **Eficiência**: Cache, otimização\n"
            tema += "5. **Manutenibilidade**: Type hints, docstrings, modularidade\n\n"
            tema += "Responda em Português do Brasil, de forma clara e objetiva."
            return tema
        except Exception as e:
            return f"Code Review do sistema (erro ao ler código: {e})"

    def _show_results(self):
        self.console.print("\n[bold green]✅ Debate concluído![/bold green]")
        historico = self.engine.get_historico()
        if historico:
            if RICH_AVAILABLE and self.console:
                self.console.print(Panel(
                    Markdown(historico[-500:]),
                    title="📊 Resumo Final",
                    border_style="green"
                ))
            else:
                print(historico[-500:])

        # Salvar em arquivo se solicitado
        if self.output_file:
            try:
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    f.write(historico)
                print(f"💾 Histórico salvo em {self.output_file}")
            except Exception as e:
                print(f"⚠️ Erro ao salvar arquivo: {e}")

# ==============================================================================
# 10. MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="4KINGS Debate Engine V3")
    parser.add_argument("--tema", help="Tema do debate (se não fornecido, perguntará)")
    parser.add_argument("--rodadas", type=int, default=3, help="Número de rodadas (padrão: 3)")
    parser.add_argument("--agentes", nargs="+", help="Lista de agentes (ex.: gemini groq ollama)")
    parser.add_argument("--output", help="Arquivo para salvar o histórico (ex.: debate.md)")
    parser.add_argument("--auto", action="store_true", help="Usa modo automático (code review)")
    args = parser.parse_args()

    # Configurar logging
    logging.basicConfig(filename='debate.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    print("\n🚀 Iniciando 4KINGS Debate Engine V3...\n")
    print("📌 AGENTES:")
    print("   🔬 Gemini (Teórico) - 800 tokens, 5 RPM")
    print("   ⚡ Groq (Prático) - 1000 tokens, 8 RPM")
    print("   🧩 Mistral (Lógico) - 600 tokens, 30 RPM")
    print("   🦙 Ollama (Local) - Ilimitado, gratuito, privado")
    print("   🤖 OpenAI (Moderno) - 800 tokens, 10 RPM")
    print("   🧠 Moderador (Síntese) - sem custos\n")

    clients = APIClients()
    if not clients.clients:
        print("\n❌ Nenhuma API configurada!")
        print("\nCrie um arquivo .env com pelo menos uma chave:")
        print("GEMINI_API_KEY=sua_chave")
        print("GROQ_API_KEY=sua_chave")
        print("MISTRAL_API_KEY=sua_chave")
        print("OPENAI_API_KEY=sua_chave")
        print("\nOU instale o Ollama para rodar localmente:")
        print("   https://ollama.ai/download")
        print("   ollama pull llama3.2")
        sys.exit(1)

    # Tratar tema
    tema = args.tema
    if args.auto:
        tema = "auto"
    if not tema and not args.tema:
        tema = None  # será perguntado na UI

    # Agentes escolhidos
    agentes_escolhidos = args.agentes if args.agentes else None

    engine = DebateEngine(clients.clients, clients.modelos, agentes_escolhidos, args.rodadas)
    ui = DebateUI(engine, output_file=args.output)

    try:
        ui.run(tema=tema, rodadas=args.rodadas)
    except KeyboardInterrupt:
        print("\n\n👋 Encerrado pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

# ==============================================================================
# 11. CLASSE APIClients (reestruturada para suportar os novos provedores)
# ==============================================================================

class APIClients:
    def __init__(self):
        self.clients = {}
        self.modelos = {}
        self.ollama_disponivel = False
        self.ollama_modelos = []
        self.load_clients()

    def load_clients(self):
        # Gemini
        key = os.environ.get('GEMINI_API_KEY')
        if not key:
            key = getpass("Chave da API Gemini (deixe vazio para não usar): ").strip() if self._perguntar("Gemini") else ""
        if key:
            try:
                self.clients['gemini'] = genai.Client(api_key=key)
                self.modelos['gemini'] = detectar_modelos_gemini(key)
                print(f"✅ Gemini configurado - modelos: {', '.join(self.modelos['gemini'][:3])}...")
            except Exception as e:
                print(f"⚠️ Gemini: {e}")

        # Groq
        key = os.environ.get('GROQ_API_KEY')
        if not key:
            key = getpass("Chave da API Groq (deixe vazio para não usar): ").strip() if self._perguntar("Groq") else ""
        if key:
            try:
                self.clients['groq'] = OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")
                self.modelos['groq'] = detectar_modelos_groq(key)
                print(f"✅ Groq configurado - modelos: {', '.join(self.modelos['groq'][:3])}...")
            except Exception as e:
                print(f"⚠️ Groq: {e}")

        # Mistral
        key = os.environ.get('MISTRAL_API_KEY')
        if not key:
            key = getpass("Chave da API Mistral (deixe vazio para não usar): ").strip() if self._perguntar("Mistral") else ""
        if key:
            try:
                self.clients['mistral'] = OpenAI(api_key=key, base_url="https://api.mistral.ai/v1")
                print("✅ Mistral AI configurado")
            except Exception as e:
                print(f"⚠️ Mistral AI: {e}")

        # OpenAI
        key = os.environ.get('OPENAI_API_KEY')
        if not key:
            key = getpass("Chave da API OpenAI (deixe vazio para não usar): ").strip() if self._perguntar("OpenAI") else ""
        if key:
            try:
                self.clients['openai'] = OpenAI(api_key=key)
                self.modelos['openai'] = detectar_modelos_openai(key)
                print(f"✅ OpenAI configurado - modelos: {', '.join(self.modelos['openai'][:3])}...")
            except Exception as e:
                print(f"⚠️ OpenAI: {e}")

        # Ollama
        self.ollama_disponivel, self.ollama_modelos = detectar_ollama()
        if self.ollama_disponivel and self.ollama_modelos:
            modelo_ollama = self.ollama_modelos[0]
            print(f"✅ Ollama configurado - modelo: {modelo_ollama}")
            self.clients['ollama'] = {
                'url': "http://localhost:11434/api/generate",
                'modelo': modelo_ollama
            }
            self.modelos['ollama'] = self.ollama_modelos
        elif self.ollama_disponivel:
            print("⚠️ Ollama está rodando, mas nenhum modelo disponível. Instale: ollama pull llama3.2")
        else:
            print("ℹ️ Ollama não disponível (local)")

    def _perguntar(self, nome):
        try:
            resposta = input(f"Deseja configurar {nome}? (s/N): ").strip().lower()
            return resposta == 's'
        except:
            return False

# ==============================================================================
# 12. EXECUÇÃO
# ==============================================================================

if __name__ == "__main__":
    main()