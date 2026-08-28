#!/usr/bin/env python
# -*- coding: utf-8 -*-


def clean_response(text: str) -> str:
    """Limpa tags <think>, rótulos de segurança e espaços extras"""
    if not text:
        return text
    
    # Remove tags <think>
    while '<think>' in text and '</think>' in text:
        start = text.find('<think>')
        end = text.find('</think>') + 8
        text = text[:start] + text[end:]
    
    # Remove rótulos de segurança
    text = text.replace('User Safety: [', '').replace(']', '')
    text = text.replace('Safety: [', '').replace(']', '')
    
    # Remove linhas vazias extras
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()