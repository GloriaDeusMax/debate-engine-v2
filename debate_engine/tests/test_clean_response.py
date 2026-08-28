#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from ..utils.clean_response import clean_response


class TestCleanResponse(unittest.TestCase):
    def test_remove_think(self):
        texto = "<think>Raciocínio interno</think>Resposta final"
        self.assertEqual(clean_response(texto), "Resposta final")

    def test_remove_think_incompleto(self):
        texto = "<think>Raciocínio sem fechamento"
        self.assertEqual(clean_response(texto), "")

    def test_remove_safety_label(self):
        texto = "User Safety: [SAFE] Resposta válida"
        self.assertIn("Resposta válida", clean_response(texto))

    def test_remove_espacos_extras(self):
        texto = "  Linha 1  \n  Linha 2  "
        self.assertEqual(clean_response(texto), "Linha 1\nLinha 2")

    def test_string_vazia(self):
        self.assertEqual(clean_response(""), "")


if __name__ == "__main__":
    unittest.main()