#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
4KINGS V2 - DEBATE ENGINE (Versão Modular Simplificada)
Tudo em um arquivo só - sem problemas de importação
"""

import os
import sys
import time
import re
import random
from datetime import datetime
from getpass import getpass
from typing import Optional, Dict, List, Tuple
from collections import deque
from abc import ABC, abstractmethod

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
# CORE - Rate Limiter
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

# ==============================================================================
# CORE - Circuit Breaker
# ==============================================================================

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

# ==============================================================================
# CORE - Cache
# ==============================================================================

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

# ==============================================================================
# UTILS - Clean Response
# ==============================================================================

def clean_response(text: str) -> str:
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
# MODELS - Model Detector (Strategy Pattern)
# ==============================================================================

class ModelStrategy(ABC):
    @abstractmethod
    def detectar(self, api_key: str) -> List[str]:
        pass

class GeminiModelStrategy(ModelStrategy):
    def detectar(self, api_key: str) -> List[str]:
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
            prioridades = ['gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-2.5-flash']
            resultado = []
            for p in prioridades:
                if p in nomes and p not in resultado:
                    resultado.append(p)
            for m in nomes:
                if m not in resultado:
                    resultado.append(m)
            return resultado
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelos Gemini: {e}")
            return ['gemini-3.6-flash', 'gemini-3.5-flash']

class GroqModelStrategy(ModelStrategy):
    def detectar(self, api_key: str) -> List[str]:
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            modelos = client.models.list()
            disponiveis = [m.id for m in modelos.data]
            chat_models = [m for m in disponiveis if not any(x in m.lower() for x in ['whisper', 'embed', 'guard', 'tts'])]
            prioridades = ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'groq/compound']
            resultado = []
            for p in prioridades:
                if p in chat_models and p not in resultado:
                    resultado.append(p)
            for m in chat_models:
                if m not in resultado:
                    resultado.append(m)
            return resultado
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelos Groq: {e}")
            return ['openai/gpt-oss-120b', 'openai/gpt-oss-20b']

class OpenRouterModelStrategy(ModelStrategy):
    def detectar(self, api_key: str) -> List[str]:
        try:
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            modelos_gratuitos = ['openrouter/free', 'nvidia/nemotron-3-nano-30b-a3b:free']
            try:
                modelos = client.models.list()
                modelos_api = [m.id for m in modelos.data]
                disponiveis = []
                for modelo in modelos_gratuitos:
                    if modelo in modelos_api:
                        disponiveis.append(modelo)
                if disponiveis:
                    return disponiveis
            except:
                pass
            return modelos_gratuitos
        except Exception as e:
            print(f"⚠️ Erro ao detectar modelos OpenRouter: {e}")
            return ['openrouter/free', 'nvidia/nemotron-3-nano-30b-a3b:free']

class ModelDetector:
    def __init__(self, provider: str):
        self.provider = provider
        self.strategy = self._get_strategy()
    
    def _get_strategy(self) -> ModelStrategy:
        if self.provider == 'gemini':
            return GeminiModelStrategy()
        elif self.provider == 'groq':
            return GroqModelStrategy()
        elif self.provider == 'openrouter':
            return OpenRouterModelStrategy()
        else:
            raise ValueError(f"Provedor {self.provider} não suportado")
    
    def detectar(self, api_key: str) -> List[str]:
        return self.strategy.detectar(api_key)

# ==============================================================================
# API - Chamadas
# ==============================================================================

def call_gemini(client, prompt, papel, modelos, max_tokens=800, temperature=0.3):
    rate_limiter = RateLimiter(max_calls_per_minute=5)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    cache = ResponseCache(max_size=50, ttl_seconds=180)
    
    cache_key = f"gemini_{hash(prompt[:200])}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
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
                cleaned = clean_response(response.text)
                cache.set(cache_key, cleaned)
                return cleaned
        except Exception as e:
            print(f"⚠️ Gemini ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                print("⏳ Rate limit, aguardando 10s...")
                time.sleep(10)
            elif "503" in str(e):
                print("⏳ Serviço indisponível, aguardando 5s...")
                time.sleep(5)
            continue
    
    cb.record_failure()
    return "[Erro Gemini: Todos os modelos falharam]"

def call_groq(client, prompt, papel, modelos, max_tokens=800, temperature=0.3):
    rate_limiter = RateLimiter(max_calls_per_minute=8)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    cache = ResponseCache(max_size=50, ttl_seconds=180)
    
    cache_key = f"groq_{hash(prompt[:200])}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
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
                temperature=temperature
            )
            content = response.choices[0].message.content
            if content and len(content) > 20:
                cb.record_success()
                cleaned = clean_response(content)
                cache.set(cache_key, cleaned)
                return cleaned
        except Exception as e:
            print(f"⚠️ Groq ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                print("⏳ Rate limit, aguardando 10s...")
                time.sleep(10)
            continue
    
    cb.record_failure()
    return "[Erro Groq: Todos os modelos falharam]"

def call_openrouter(client, prompt, papel, modelos, max_tokens=800, temperature=0.3):
    rate_limiter = RateLimiter(max_calls_per_minute=5)
    cb = CircuitBreaker(failure_threshold=3, timeout=120)
    cache = ResponseCache(max_size=50, ttl_seconds=180)
    
    cache_key = f"openrouter_{hash(prompt[:200])}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    rate_limiter.wait()
    if not cb.can_execute():
        return "[Circuit Breaker: OpenRouter indisponível]"
    
    for modelo in modelos:
        try:
            print(f"🔄 Tentando OpenRouter: {modelo}")
            response = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": papel},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                extra_headers={
                    "HTTP-Referer": "https://localhost",
                    "X-Title": "4KINGS Debate"
                }
            )
            content = response.choices[0].message.content
            if content and len(content) > 20:
                cb.record_success()
                cleaned = clean_response(content)
                cache.set(cache_key, cleaned)
                return cleaned
        except Exception as e:
            print(f"⚠️ OpenRouter ({modelo}): {str(e)[:60]}")
            if "429" in str(e):
                print("⏳ Rate limit, aguardando 10s...")
                time.sleep(10)
            continue
    
    cb.record_failure()
    return "[Erro OpenRouter: Todos os modelos falharam]"

# ==============================================================================
# CONFIGURAÇÃO
# ==============================================================================

INSTRUCAO_IDIOMA = "Responda SEMPRE em português do Brasil. Nunca responda em inglês."

PAPEIS = {
    'gemini': f"Especialista Teórico - Fundamente com frameworks, conceitos e teoria. {INSTRUCAO_IDIOMA}",
    'groq': f"Engenheiro Prático - Dê soluções concretas, exemplos práticos e código. {INSTRUCAO_IDIOMA}",
    'nemotron': f"Crítico Adversarial - Aponte falhas lógicas, contradições e pontos fracos. Seja incisivo, mas construtivo. {INSTRUCAO_IDIOMA}",
    'curinga': f"Sintetizador - Una os argumentos, aponte convergências e divergências, sugira o próximo passo. {INSTRUCAO_IDIOMA}"
}

CORES = {
    'gemini': 'blue',
    'groq': 'green',
    'nemotron': 'orange1',
    'curinga': 'magenta'
}

EMOJIS = {
    'gemini': '🔬',
    'groq': '⚡',
    'nemotron': '🔍',
    'curinga': '🔄'
}

PAPEIS_DISPLAY = {
    'gemini': 'Teórico',
    'groq': 'Prático',
    'nemotron': 'Crítico',
    'curinga': 'Sintetizador'
}

# ==============================================================================
# CLIENTES
# ==============================================================================

class APIClients:
    def __init__(self):
        self.clients = {}
        self.modelos = {}
        self.load_clients()
        
    def load_clients(self):
        keys = {
            'gemini': os.environ.get('GEMINI_API_KEY'),
            'groq': os.environ.get('GROQ_API_KEY'),
            'openrouter': os.environ.get('OPENROUTER_API_KEY'),
        }
        
        for provider, key in keys.items():
            if not key:
                keys[provider] = getpass(f"Chave da API {provider.capitalize()}: ").strip()
        
        if keys['gemini']:
            try:
                self.clients['gemini'] = genai.Client(api_key=keys['gemini'])
                detector = ModelDetector('gemini')
                self.modelos['gemini'] = detector.detectar(keys['gemini'])
                print(f"✅ Gemini configurado - modelos: {', '.join(self.modelos['gemini'][:3])}...")
            except Exception as e:
                print(f"⚠️ Gemini: {e}")
        
        if keys['groq']:
            try:
                self.clients['groq'] = OpenAI(api_key=keys['groq'], base_url="https://api.groq.com/openai/v1")
                detector = ModelDetector('groq')
                self.modelos['groq'] = detector.detectar(keys['groq'])
                print(f"✅ Groq configurado - modelos: {', '.join(self.modelos['groq'][:3])}...")
            except Exception as e:
                print(f"⚠️ Groq: {e}")
        
        if keys['openrouter']:
            try:
                self.clients['openrouter'] = OpenAI(api_key=keys['openrouter'], base_url="https://openrouter.ai/api/v1")
                detector = ModelDetector('openrouter')
                self.modelos['openrouter'] = detector.detectar(keys['openrouter'])
                print(f"✅ OpenRouter configurado - modelos: {', '.join(self.modelos['openrouter'][:3])}...")
            except Exception as e:
                print(f"⚠️ OpenRouter: {e}")

# ==============================================================================
# PROMPT BUILDER
# ==============================================================================

class PromptBuilder:
    def build_prompt(self, tema, resumo, falas, agente, max_historico=3):
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
# DEBATE ENGINE
# ==============================================================================

class DebateEngine:
    def __init__(self, clients, modelos):
        self.clients = clients
        self.modelos = modelos
        self.prompt_builder = PromptBuilder()
        self.historico = ""
        self.resumo = ""
        self.falas = []
        self.todas_falas = []
        self.agentes_ativos = []
        
        if 'gemini' in self.clients:
            self.agentes_ativos.append('gemini')
        if 'groq' in self.clients:
            self.agentes_ativos.append('groq')
        if 'openrouter' in self.clients:
            self.agentes_ativos.append('nemotron')
            self.agentes_ativos.append('curinga')
    
    def run_round(self, tema, round_num):
        print(f"\n{'='*60}")
        print(f"RODADA {round_num}")
        print('='*60)
        
        ordem = self.agentes_ativos.copy()
        random.shuffle(ordem)
        
        respostas = {}
        
        for agente in ordem:
            if agente == 'nemotron':
                client = self.clients.get('openrouter')
                modelos = self.modelos.get('openrouter', ['nvidia/nemotron-3-nano-30b-a3b:free'])
                papel = PAPEIS['nemotron']
                func = call_openrouter
            elif agente == 'curinga':
                client = self.clients.get('openrouter')
                modelos = self.modelos.get('openrouter', ['openrouter/free'])
                papel = PAPEIS['curinga']
                func = call_openrouter
            elif agente == 'gemini':
                client = self.clients.get('gemini')
                modelos = self.modelos.get('gemini', ['gemini-3.6-flash'])
                papel = PAPEIS['gemini']
                func = call_gemini
            elif agente == 'groq':
                client = self.clients.get('groq')
                modelos = self.modelos.get('groq', ['openai/gpt-oss-120b'])
                papel = PAPEIS['groq']
                func = call_groq
            else:
                continue
            
            if not client:
                continue
            
            prompt = self.prompt_builder.build_prompt(tema, self.resumo, self.falas, agente)
            
            cor = CORES.get(agente, 'white')
            emoji = EMOJIS.get(agente, '🤖')
            print(f"\n[bold {cor}]{emoji} {agente.capitalize()} pensando...[/bold {cor}]")
            
            resposta = func(client, prompt, papel, modelos, max_tokens=800, temperature=0.3)
            
            if not resposta.startswith("[Erro") and not resposta.startswith("[Circuit Breaker"):
                self.falas.append((agente, resposta))
                self.todas_falas.append((agente, resposta))
                self.historico += f"\n[{agente}]: {resposta}\n"
                respostas[agente] = resposta
                
                cor = CORES.get(agente, 'white')
                emoji = EMOJIS.get(agente, '🤖')
                nome = agente.capitalize()
                resp_display = resposta[:500] + ("..." if len(resposta) > 500 else "")
                print(f"\n[bold {cor}]{emoji} {nome}:[/bold {cor}]")
                print(resp_display)
                print("-"*40)
            else:
                print(f"\n⚠️ {agente.capitalize()} falhou: {resposta[:100]}")
            
            time.sleep(2)
        
        self.resumo = self._gerar_resumo()
        self.falas = []
        
        return respostas
    
    def _gerar_resumo(self):
        if not self.todas_falas:
            return self.resumo
        ultimas = self.todas_falas[-6:]
        resumo = "Pontos principais: " + "; ".join([
            f"{nome}: {texto[:80]}..." for nome, texto in ultimas
        ])
        return resumo[:300]
    
    def get_historico(self):
        return self.historico

# ==============================================================================
# UI
# ==============================================================================

class DebateUI:
    def __init__(self, engine):
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
            "[dim]Versão Modular Simplificada[/dim]",
            border_style="cyan"
        ))
        
        table = Table(title="🤖 Agentes do Debate", box=box.ROUNDED)
        table.add_column("Agente", style="cyan")
        table.add_column("Papel", style="yellow")
        table.add_column("Modelo Ativo", style="green")
        table.add_column("Status", style="white")
        
        for agente in self.engine.agentes_ativos:
            papel = PAPEIS_DISPLAY.get(agente, "N/A")
            emoji = EMOJIS.get(agente, '🤖')
            
            if agente == 'gemini' and agente in self.engine.modelos:
                modelo = self.engine.modelos['gemini'][0] if self.engine.modelos['gemini'] else 'N/A'
            elif agente == 'groq' and agente in self.engine.modelos:
                modelo = self.engine.modelos['groq'][0] if self.engine.modelos['groq'] else 'N/A'
            elif agente == 'nemotron' and 'openrouter' in self.engine.modelos:
                modelo = self.engine.modelos['openrouter'][0] if self.engine.modelos['openrouter'] else 'N/A'
            elif agente == 'curinga' and 'openrouter' in self.engine.modelos:
                modelo = self.engine.modelos['openrouter'][0] if self.engine.modelos['openrouter'] else 'N/A'
            else:
                modelo = 'N/A'
            
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
                task = progress.add_task(f"[cyan]Rodada {rodada}...", total=None)
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
            tema += "1. **Arquitetura**: Estrutura de classes, padrões de design\n"
            tema += "2. **Tratamento de Erros**: Robustez, fallbacks, circuit breakers\n"
            tema += "3. **Segurança**: Sanitização, mascaramento de chaves\n"
            tema += "4. **Eficiência**: Cache, chamadas assíncronas, otimização\n"
            tema += "5. **Manutenibilidade**: Type hints, docstrings, modularidade\n\n"
            tema += "Responda em Português do Brasil, de forma clara e objetiva."
            
            return tema
        except Exception as e:
            return f"Code Review do sistema (erro ao ler código: {e})"
    
    def _show_results(self):
        self.console.print("\n[bold green]✅ Debate concluído![/bold green]")
        
        historico = self.engine.get_historico()
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
# MAIN
# ==============================================================================

def main():
    print("\n🚀 Iniciando 4KINGS Debate Engine (Versão Modular Simplificada)...\n")
    print("📌 CARACTERÍSTICAS:")
    print("   ✅ Strategy Pattern para detecção de modelos")
    print("   ✅ Visual arrojado com cores e emojis")
    print("   ✅ Tudo em um arquivo só (sem problemas de importação)\n")
    
    clients = APIClients()
    
    if not clients.clients:
        print("\n❌ Nenhuma API configurada!")
        print("\nCrie um arquivo .env com:")
        print("GEMINI_API_KEY=sua_chave")
        print("GROQ_API_KEY=sua_chave")
        print("OPENROUTER_API_KEY=sua_chave")
        sys.exit(1)
    
    engine = DebateEngine(clients.clients, clients.modelos)
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