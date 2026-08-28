#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from ..circuit_breaker import CircuitBreaker


class TestCircuitBreaker(unittest.TestCase):
    def test_closed_to_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, timeout=1)
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state.state, "OPEN")
        self.assertFalse(cb.can_execute())

    def test_open_to_half_open_after_timeout(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, timeout=0.1)
        cb.record_failure()
        cb.record_failure()
        # Simular espera
        import time
        time.sleep(0.2)
        self.assertTrue(cb.can_execute())  # deve passar para HALF_OPEN

    def test_success_resets(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)
        cb.record_success()
        self.assertEqual(cb.state.consecutive_failures, 0)
        self.assertEqual(cb.state.state, "CLOSED")


if __name__ == "__main__":
    unittest.main()