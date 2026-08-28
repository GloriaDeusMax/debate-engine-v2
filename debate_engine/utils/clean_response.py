#!/usr/bin/env python
# -*- coding: utf-8 -*-

def clean_response(text: str) -> str:
    """
    Limpa tags <think> e espaços extras.

    Se houver um bloco <think> sem fechamento </think>, retorna uma string vazia.
    Isso indica que a resposta foi truncada no meio do raciocínio interno e não
    deve ser considerada válida (aciona retry/fallback).
    """
    if not text:
        return ""

    # Se o bloco <think> foi aberto mas nunca fechado, a resposta é inválida
    if "<think>" in text and "</think>" not in text:
        return ""

    # Remove todos os blocos <think>...</think> completos
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>") + len("</think>")
        text = text[:start] + text[end:]

    # Remove rótulos de segurança
    text = text.replace("User Safety: [", "").replace("]", "")
    text = text.replace("Safety: [", "").replace("]", "")

    # Remove linhas vazias e espaços extras
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)

    return text.strip()