#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict

INSTRUCAO_IDIOMA = "Responda SEMPRE em português do Brasil. Nunca responda em inglês."

# Papéis para provedores que NÃO têm especialidades internas (Gemini, Groq, OpenRouter, Ollama)
PAPEIS_PADRAO: Dict[str, str] = {
    'gemini': f"Especialista Teórico - Fundamente com frameworks, conceitos e teoria. {INSTRUCAO_IDIOMA}",
    'groq': f"Engenheiro Prático - Dê soluções concretas, exemplos práticos e código. {INSTRUCAO_IDIOMA}",
    'openrouter': f"Assistente Versátil - Conhecimento amplo e adaptável. {INSTRUCAO_IDIOMA}",
    'ollama_llama3_2_latest': f"Generalista Ágil - Respostas rápidas, diretas e equilibradas. {INSTRUCAO_IDIOMA}",
    
    # Nvidia agora tem especialidades internas; usamos um placeholder vazio para evitar conflito
    'nvidia': "",
    
    # Novos provedores (Mistral e Cerebras)
    'mistral': f"Especialista em Raciocínio Lógico - Análise profunda e estruturada. {INSTRUCAO_IDIOMA}",
    'cerebras': f"Especialista em Velocidade - Respostas rápidas e diretas. {INSTRUCAO_IDIOMA}",
}

# Cores e emojis
CORES: Dict[str, str] = {
    'gemini': 'blue',
    'groq': 'green',
    'openrouter': 'cyan',
    'nvidia': 'magenta',
    'ollama_llama3_2_latest': 'white',
}

EMOJIS: Dict[str, str] = {
    'gemini': '🔬',
    'groq': '⚡',
    'openrouter': '🤖',
    'nvidia': '🚀',
    'ollama_llama3_2_latest': '✨',
}

class PromptBuilder:
    def get_papel(self, nome_agente: str) -> str:
        # Se o papel for vazio, usa um genérico
        papel = PAPEIS_PADRAO.get(nome_agente, "")
        if not papel:
            papel = f"Assistente especializado. {INSTRUCAO_IDIOMA}"
        return papel
    
    def get_cor(self, nome_agente: str) -> str:
        return CORES.get(nome_agente, 'white')
    
    def get_emoji(self, nome_agente: str) -> str:
        return EMOJIS.get(nome_agente, '🤖')
    
    def build_prompt(self, tema, resumo, falas, agente, max_historico=3):
        falas_recentes = falas[-max_historico:] if falas else []
        falas_txt = "\n".join(f"[{n}]: {t[:200]}" for n, t in falas_recentes) if falas_recentes else "Nenhuma contribuição ainda."
        papel = self.get_papel(agente)
        return f"""{papel}

Tema: {tema}

Resumo Atual:
{resumo or "Início do debate."}

Últimas Contribuições:
{falas_txt}

Sua Resposta (seja direto e objetivo):"""


prompt_builder = PromptBuilder()