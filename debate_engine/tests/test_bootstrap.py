#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch
from ..bootstrap import verificar_dependencias


class TestVerificarDependencias(unittest.TestCase):
    @patch("importlib.import_module")
    def test_dependencias_ok(self, mock_import):
        mock_import.return_value = True
        verificar_dependencias()  # não deve lançar exceção

    @patch("importlib.import_module")
    def test_dependencia_faltando(self, mock_import):
        mock_import.side_effect = ImportError
        with self.assertRaises(Exception):
            verificar_dependencias()


if __name__ == "__main__":
    unittest.main()