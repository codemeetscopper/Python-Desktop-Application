import unittest
from unittest.mock import patch, MagicMock
from common.logger import Logger  # Replace with actual module name
import logging
class TestLogger(unittest.TestCase):

    def setUp(self):
        # Reset the singleton instance before each test
        Logger._instance = None

    def test_singleton_behavior(self):
        logger1 = Logger()
        logger2 = Logger()
        self.assertIs(logger1, logger2)

    def test_log_storage_and_signal_emission(self):
        logger = Logger()
        mock_slot = MagicMock()
        logger.log_updated.connect(mock_slot)

        msg = "Test info message"
        formatted = logger.info(msg)

        self.assertIn("INFO", formatted)
        self.assertIn(msg, formatted)
        self.assertIn(formatted, logger.logs)
        mock_slot.assert_called_once_with(msg)

    def test_debug_does_not_emit_signal(self):
        logger = Logger()
        mock_slot = MagicMock()
        logger.log_updated.connect(mock_slot)

        msg = "Test debug message"
        formatted = logger.debug(msg)

        self.assertIn("DEBUG", formatted)
        self.assertIn(msg, formatted)
        self.assertIn(formatted, logger.logs)
        mock_slot.assert_not_called()

    def test_log_function_decorator(self):
        logger = Logger()

        @logger.log_function(level=logging.INFO)
        def sample_func(x, y):
            return x + y

        result = sample_func(2, 3)
        self.assertEqual(result, 5)
        self.assertTrue(any("Calling sample_func" in log for log in logger.logs))
        self.assertTrue(any("sample_func returned 5" in log for log in logger.logs))

    def test_export_to_file(self):
        import os
        logger = Logger()
        logger.info("Export test message")
        test_file = "test_log_output.txt"

        logger.export_to_file(test_file)

        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Export test message", content)

        os.remove(test_file)