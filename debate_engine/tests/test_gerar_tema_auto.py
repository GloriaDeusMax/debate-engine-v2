#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes para o módulo utils/gerar_tema_auto.py.
Executar com: python -m pytest debate_engine/tests/test_gerar_tema_auto.py -v
"""

import unittest
from pathlib import Path
from ..utils.gerar_tema_auto import sanitizar_codigo, gerar_tema_auto


class TestSanitizarCodigo(unittest.TestCase):
    def test_mascarar_api_key(self):
        original = 'api_key = "sk-abcdefghijklmnopqrstuvwxyz"'
        resultado = sanitizar_codigo(original)
        self.assertIn("***MASKED***", resultado)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", resultado)

    def test_mascarar_gemini_key(self):
        original = 'GEMINI_KEY = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"'
        resultado = sanitizar_codigo(original)
        self.assertIn("***MASKED_KEY***", resultado)
        self.assertNotIn("AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ", resultado)

    def test_mascarar_com_type_hint(self):
        original = 'password: str = "minhasenha123"'
        resultado = sanitizar_codigo(original)
        self.assertIn("***MASKED***", resultado)
        self.assertNotIn("minhasenha123", resultado)

    def test_nao_mascarar_os_getenv(self):
        original = 'token = os.getenv("TOKEN")'
        resultado = sanitizar_codigo(original)
        self.assertEqual(original, resultado)


class TestGerarTemaAuto(unittest.TestCase):
    def test_gerar_tema_auto_retorna_string(self):
        tema = gerar_tema_auto()
        self.assertIsInstance(tema, str)
        self.assertIn("CODE REVIEW", tema)
        self.assertIn("Código Real do Projeto", tema)


if __name__ == "__main__":
    unittest.main()