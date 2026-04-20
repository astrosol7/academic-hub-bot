import unittest
from unittest.mock import patch

from src.core.config import load_config


class ConfigTests(unittest.TestCase):
    def test_invalid_index_memory_env_raises_clear_error(self) -> None:
        with patch.dict("os.environ", {"ACADEMIC_HUB_MAX_INDEX_MEMORY_MB": "not-a-number"}, clear=False):
            with self.assertRaises(RuntimeError):
                load_config(require_token=False)
