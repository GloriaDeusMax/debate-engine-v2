#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes para a função de sanitização de código do DebateEngine.
Executar com: python -m pytest debate_engine/tests/test_sanitizacao.py
"""

import re
import unittest

# Importa a função diretamente do ui (ou pode ser movida para utils/clean_response.py)
from ..ui import DebateUI


class TestSanitizacao(unittest.TestCase):
    def setUp(self):
        # Instancia sem precisar do orchestrator
        self.ui = DebateUI.__new__(DebateUI)

    def test_mascarar_api_key(self):
        original = 'api_key = "sk-abcdefghijklmnopqrstuvwxyz"'
        resultado = self.ui._sanitizar_codigo(original)
        self.assertIn("***MASKED***", resultado)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz", resultado)

    def test_mascarar_gemini_key(self):
        original = 'GEMINI_KEY = "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234567"'
        resultado = self.ui._sanitizar_codigo(original)
        self.assertIn("***MASKED_KEY***", resultado)
        self.assertNotIn("AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ", resultado)

    def test_mascarar_com_type_hint(self):
        original = 'password: str = "minhasenha123"'
        resultado = self.ui._sanitizar_codigo(original)
        self.assertIn("***MASKED***", resultado)
        self.assertNotIn("minhasenha123", resultado)

    def test_nao_mascarar_os_getenv(self):
        original = 'token = os.getenv("TOKEN")'
        resultado = self.ui._sanitizar_codigo(original)
        self.assertEqual(original, resultado)

    def test_mascarar_api_key_com_type_hint(self):
        original = 'api_key: str = "outra_chave_aqui"'
        resultado = self.ui._sanitizar_codigo(original)
        self.assertIn("***MASKED***", resultado)


if __name__ == "__main__":
    unittest.main()