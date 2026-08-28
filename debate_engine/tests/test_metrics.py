#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testes para o módulo metrics.py.

Executar com:
python -m pytest debate_engine/tests/test_metrics.py -v
"""

import unittest
from ..metrics import metrics, MetricsCollector


class TestMetricsCollector(unittest.TestCase):
    """Testa a classe MetricsCollector diretamente."""

    def setUp(self):
        # Instancia um coletor isolado para não interferir no global
        self.collector = MetricsCollector()

    def test_registrar_debate(self):
        """record_debate deve adicionar um debate à lista."""
        self.collector.record_debate(tema="Teste", rounds=2, messages=10)
        self.assertEqual(len(self.collector.metrics['debates']), 1)
        self.assertEqual(self.collector.metrics['debates'][0]['tema'], "Teste")
        self.assertEqual(self.collector.metrics['debates'][0]['rounds'], 2)

    def test_registrar_api_call_sucesso(self):
        """record_api_call deve registrar uma chamada bem-sucedida."""
        self.collector.record_api_call(
            provider="gemini", model="gemini-3.6-flash",
            success=True, response_time=0.2, tokens=100, error=None
        )
        chamadas = self.collector.metrics['api_calls']['gemini']
        self.assertEqual(len(chamadas), 1)
        self.assertEqual(chamadas[0]['success'], True)
        self.assertEqual(chamadas[0]['tokens'], 100)

    def test_registrar_api_call_erro(self):
        """record_api_call deve registrar erro e incrementar contador."""
        self.collector.record_api_call(
            provider="groq", model="gpt-oss-120b",
            success=False, response_time=0.5, tokens=0, error="429"
        )
        self.assertEqual(self.collector.metrics['errors']['groq'], 1)
        self.assertEqual(self.collector.metrics['tokens_used']['groq'], 0)

    def test_get_summary_contem_chaves(self):
        """get_summary deve retornar dicionário com chaves esperadas."""
        resumo = self.collector.get_summary()
        chaves = ["total_debates", "total_api_calls", "total_errors", "error_rate",
                  "uptime_seconds", "providers", "avg_response_time", "recent_debates"]
        for chave in chaves:
            self.assertIn(chave, resumo)

    def test_get_summary_valores(self):
        """get_summary deve refletir as métricas registradas."""
        self.collector.record_debate(tema="IA", rounds=1, messages=3)
        self.collector.record_api_call(
            provider="openrouter", model="auto",
            success=True, response_time=0.1, tokens=10, error=None
        )
        self.collector.record_api_call(
            provider="openrouter", model="auto",
            success=False, response_time=0.3, tokens=0, error="429"
        )
        resumo = self.collector.get_summary()
        self.assertEqual(resumo['total_debates'], 1)
        self.assertEqual(resumo['total_api_calls'], 2)
        self.assertEqual(resumo['total_errors'], 1)
        self.assertGreater(resumo['uptime_seconds'], 0)

    def test_get_provider_metrics(self):
        """get_provider_metrics deve retornar métricas de um provedor."""
        self.collector.record_api_call(
            provider="nvidia", model="nemotron", success=True,
            response_time=0.4, tokens=50, error=None
        )
        self.collector.record_api_call(
            provider="nvidia", model="nemotron", success=True,
            response_time=0.6, tokens=80, error=None
        )
        info = self.collector.get_provider_metrics("nvidia")
        self.assertEqual(info['total_calls'], 2)
        self.assertEqual(info['successful'], 2)
        self.assertEqual(info['failed'], 0)
        self.assertAlmostEqual(info['avg_response_time'], 0.5, places=1)
        self.assertEqual(info['total_tokens'], 130)

    def test_get_provider_metrics_vazio(self):
        """get_provider_metrics deve retornar {} para provedor sem chamadas."""
        info = self.collector.get_provider_metrics("inexistente")
        self.assertEqual(info, {})


class TestMetricsGlobal(unittest.TestCase):
    """Testa o objeto global metrics."""

    def test_metrics_global_existe(self):
        """O objeto metrics deve estar disponível."""
        self.assertIsInstance(metrics, MetricsCollector)

    def test_get_summary_global(self):
        """get_summary do global deve retornar dict."""
        resumo = metrics.get_summary()
        self.assertIsInstance(resumo, dict)


if __name__ == "__main__":
    unittest.main()