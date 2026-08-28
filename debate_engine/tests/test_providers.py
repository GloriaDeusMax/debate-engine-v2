#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch
from ..providers.base import BaseProvider


class MockProvider(BaseProvider):
    """Subclasse concreta para testar métodos da BaseProvider."""
    def __init__(self, nome="test", modelos=None, rate_limit=8):
        super().__init__(nome=nome, modelos=modelos or ["modelo1"], rate_limit=rate_limit)

    def call(self, prompt, papel, max_tokens=800, temperature=0.3):
        return "resposta mock"

    def get_nome(self):
        return self._nome

    def get_modelo_atual(self):
        return self._modelo_atual

    def get_modelos_disponiveis(self):
        return self._modelos


class TestBaseProvider(unittest.TestCase):
    def test_gerar_cache_key(self):
        provider = MockProvider(nome="test", modelos=["modelo1"])
        key1 = provider._gerar_cache_key("prompt teste")
        key2 = provider._gerar_cache_key("prompt teste")
        self.assertEqual(key1, key2)

    def test_executar_com_resiliencia_sucesso(self):
        provider = MockProvider(nome="test", modelos=["modelo1"])
        provider._executar_com_resiliencia = MagicMock(return_value="resposta")
        resultado = provider._executar_com_resiliencia("prompt", lambda: "resposta")
        self.assertEqual(resultado, "resposta")

    def test_get_modelos_disponiveis(self):
        provider = MockProvider(nome="test", modelos=["modelo1", "modelo2"])
        self.assertEqual(provider.get_modelos_disponiveis(), ["modelo1", "modelo2"])


class TestProviders(unittest.TestCase):
    def test_factory_criar_provedores(self):
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            from ..providers.factory import criar_provedores
            providers = criar_provedores()
            self.assertIn('gemini', providers)


if __name__ == "__main__":
    unittest.main()