\# 🎙️ 4KINGS Debate Engine V2



Sistema multi‑agente que promove \*\*debates automáticos entre diferentes LLMs\*\* para revisão de código, análise de arquitetura, geração de ideias e evolução de projetos.



Os agentes (Gemini, Groq, OpenRouter, NVIDIA e Ollama) discutem um tema, cada um com um papel específico, e geram um resumo final. Você pode interagir e pedir que continuem a conversa.



\---



\## 📋 Funcionalidades



\- \*\*Debate multi‑agente\*\* com 5 provedores de LLM:

&#x20; - 🔬 \*\*Gemini\*\* – Especialista Teórico

&#x20; - ⚡ \*\*Groq\*\* – Engenheiro Prático

&#x20; - 🤖 \*\*OpenRouter\*\* – Assistente Versátil

&#x20; - 🚀 \*\*NVIDIA\*\* – Especialistas em diferentes áreas (rápido/profundo)

&#x20; - ✨ \*\*Ollama\*\* – Analista Local (offline)

\- \*\*Modo AUTO\*\* – Gera um Code Review do próprio projeto (lê código real, com sanitização de chaves)

\- \*\*Fallback automático\*\* – Se um modelo falhar, tenta outro da lista

\- \*\*Retry com backoff\*\* – Para erros transitórios (rate limit, indisponibilidade)

\- \*\*Circuit Breaker\*\* – Evita sobrecarga em provedores instáveis

\- \*\*Chat interativo\*\* – Após o debate, envie mensagens e os agentes respondem com contexto

\- \*\*Sanitização de segredos\*\* – Chaves de API, tokens e senhas são mascarados antes de enviar a LLMs externos

\- \*\*CLI e UI interativa\*\* – Execute via linha de comando ou menu interativo

\- \*\*Testes unitários\*\* – Para sanitização e lógica central



\---



\## 🚀 Instalação



\### 1. Clone ou copie o projeto para sua máquina



```bash

git clone <seu-repositorio> # ou copie a pasta projeto\_debate

cd projeto\_debate

