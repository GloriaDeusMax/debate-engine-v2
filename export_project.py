#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exporta a estrutura do projeto e o código-fonte para um arquivo de texto,
útil para enviar a outra IA (ex: Claude, ChatGPT) para análise.
"""

import os
import sys
from pathlib import Path


def export_tree(base_path: Path, indent: str = "", exclude: list = None) -> str:
    """Gera uma árvore de diretórios."""
    exclude = exclude or [".git", "__pycache__", ".env", "logs", "cache", "venv", ".pytest_cache"]
    result = []
    items = sorted(base_path.iterdir(), key=lambda x: (x.is_file(), x.name))
    for item in items:
        if item.name in exclude:
            continue
        if item.is_dir():
            result.append(f"{indent}📁 {item.name}/")
            result.append(export_tree(item, indent + "  ", exclude))
        else:
            size = item.stat().st_size
            result.append(f"{indent}📄 {item.name} ({size} bytes)")
    return "\n".join(result)


def export_code(base_path: Path, output_file: Path):
    """Exporta todos os arquivos .py concatenados em um único arquivo."""
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# ESTRUTURA DO PROJETO\n")
        out.write(export_tree(base_path))
        out.write("\n\n# CÓDIGO-FONTE COMPLETO\n")

        # Lista de arquivos .py a incluir (exclui venv e testes opcionais)
        py_files = [p for p in base_path.rglob("*.py") if "venv" not in str(p) and ".pytest_cache" not in str(p)]

        for py_file in sorted(py_files):
            if "export_project" in str(py_file):
                continue
            out.write(f"\n\n{'='*80}\n")
            out.write(f"# ARQUIVO: {py_file.relative_to(base_path)}\n")
            out.write(f"{'='*80}\n\n")
            with open(py_file, 'r', encoding='utf-8') as f:
                out.write(f.read())

    print(f"✅ Projeto exportado para {output_file}")
    print(f"   Tamanho: {output_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    output = base / "projeto_completo.txt"
    export_code(base, output)
    print("Use o arquivo 'projeto_completo.txt' para colar em outra IA.")