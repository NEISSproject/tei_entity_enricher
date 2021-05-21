import unittest
import tempfile
from tei_entity_enricher.interface.gnd.identifier import Identifier

class TestGNDConnector(unittest.TestCase):
    #auxiliaries
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()  # use this dir for tests
    def tearDown(self):
        self.tempdir.cleanup()  # remove temp dir after all tests of this class are done
    def get_identifiers(self):
        input_single = [('Berlin', 'place')]
        input_multiple = [('Berlin', 'place'), ('Uwe Johnson', 'person')]
        return [Identifier(input_data, False) for input_data in [input_single, input_multiple]]

    #tests
    def test_init(self):
        for identifier in self.get_identifiers():
            self.assertIsInstance(identifier, Identifier, "variable con should refer to an instance of Identifier class")
            self.assertEqual(type(identifier.input[0]), tuple, "entry of input list should be of type tuple")
    def test_get_wikidata_search_results(self):
        for identifier in self.get_identifiers():
            result = identifier.get_wikidata_search_results()
            self.assertIsInstance(result, dict, "return value type of get_wikidata_search_results() should be dict")
            self.assertIsInstance(result[list(result.keys())[0]], list, "from get_wikidata_search_results() returned dict should have lists as its values")
            self.assertIsInstance(result[list(result.keys())[0]][0], int, "from get_wikidata_search_results() returned lists in dict should have an integer value on index 0")
            self.assertIsInstance(result[list(result.keys())[0]][1], int, "from get_wikidata_search_results() returned lists in dict should have an dict value on index 1")

if __name__ == '__main__':
    unittest.main()