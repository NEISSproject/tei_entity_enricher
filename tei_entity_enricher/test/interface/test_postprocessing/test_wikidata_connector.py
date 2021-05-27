import unittest
import tempfile
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector

class TestPostprocessingWikidataConnector(unittest.TestCase):
    #auxiliaries
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()  # use this dir for tests
    def tearDown(self):
        self.tempdir.cleanup()  # remove temp dir after all tests of this class are done
    def get_connectors(self):
        return [WikidataConnector([('Berlin', 'place')], True, True)]

    #tests
    def test_init(self):
        for connector in self.get_connectors():
            self.assertIsInstance(connector, WikidataConnector, "variable con should refer to an instance of WikidataConnector class")
            self.assertEqual(type(connector.input[0]), tuple, "entry of input list should be of type tuple")
    def test_connectivity_check(self):
        for connector in self.get_connectors():
            self.assertEqual(type(connector.connectivity_check()), int, "connectivity_check() should return integer value")
    def test_get_wikidata_search_results(self):
        for connector in self.get_connectors():
            result = connector.get_wikidata_search_results()
            self.assertIsInstance(result, dict, "return value type of get_wikidata_search_results() should be dict")
            self.assertIsInstance(result[list(result.keys())[0]], list, "from get_wikidata_search_results() returned dict should have lists as its values")
            self.assertIsInstance(result[list(result.keys())[0]][0], int, "from get_wikidata_search_results() returned lists in dict should have an integer value on index 0")
            self.assertIsInstance(result[list(result.keys())[0]][1], dict, "from get_wikidata_search_results() returned lists in dict should have an dict value on index 1")

if __name__ == '__main__':
    unittest.main()