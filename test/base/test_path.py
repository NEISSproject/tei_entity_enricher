import os.path
import unittest

from tei_entity_enricher.util.helper import module_path


class TestPath(unittest.TestCase):
    def test_module_path(self):
        assert os.path.basename(module_path) == "tei_entity_enricher", f"module path should point into 'tei_entity_enricher' but is: {module_path}"

    def test_menu_config_path(self):
        for config_dir in ["NTD", "TNM", "TR_Configs"]:
            test_dir = os.path.join(module_path, 'templates', config_dir)
            assert os.path.isdir(test_dir), f"{test_dir} is not a directory"