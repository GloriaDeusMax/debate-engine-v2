#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock
from ..orchestrator import RealOrchestrator, DebateState
from ..config import config


class MockProvider:
    def __init__(self, nome="mock", modelo="modelo1"):
        self._nome = nome
        self._modelo_atual = modelo

    def call(self, prompt, papel="", max_tokens=800, temperature=0.3):
        return f"Resposta de {self._nome}"

    def get_nome(self):
        return self._nome

    def get_modelo_atual(self):
        return self._modelo_atual

    def get_modelos_disponiveis(self):
        return [self._modelo_atual]


class TestDebateState(unittest.TestCase):
    def test_add_fala(self):
        state = DebateState()
        state.add_fala("gemini", "Olá")
        self.assertEqual(len(state.todas_falas), 1)
        self.assertIn("gemini", state.historico)
        self.assertIn("Olá", state.historico)

    def test_clear_rodada(self):
        state = DebateState()
        state.add_fala("groq", "Oi")
        state.clear_rodada()
        self.assertEqual(state.falas_rodada, [])


class TestRealOrchestrator(unittest.TestCase):
    def setUp(self):
        self.providers = {
            "gemini": MockProvider("gemini"),
            "groq": MockProvider("groq"),
        }
        self.orch = RealOrchestrator(providers=self.providers)

    def test_run_round(self):
        respostas = self.orch.run_round("teste", 1)
        self.assertIn("gemini", respostas)
        self.assertIn("groq", respostas)
        self.assertIn("Resposta de gemini", respostas["gemini"])

    def test_get_debate_summary(self):
        self.assertEqual(self.orch.get_debate_summary(), "Nenhum histórico disponível.")

    def test_continuar_chat(self):
        respostas = self.orch.continuar_chat("continuem", incluir_historico=False)
        self.assertIn("gemini", respostas)


if __name__ == "__main__":
    unittest.main()