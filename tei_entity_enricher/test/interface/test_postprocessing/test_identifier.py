import unittest
import tempfile
from tei_entity_enricher.interface.postprocessing.identifier import Identifier


class TestPostprocessingIdentifier(unittest.TestCase):
    # auxiliaries
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()  # use this dir for tests

    def tearDown(self):
        self.tempdir.cleanup()  # remove temp dir after all tests of this class are done

    def get_identifiers(self):
        return [Identifier([("Berlin", "place")], True)]

    # tests
    def test_init(self):
        for identifier in self.get_identifiers():
            self.assertIsInstance(
                identifier,
                Identifier,
                "variable con should refer to an instance of Identifier class",
            )
            self.assertEqual(
                type(identifier.input[0]),
                tuple,
                "entry of input list should be of type tuple",
            )

    def test_query(self):
        for identifier in self.get_identifiers():
            result = identifier.query()
            self.assertIsInstance(
                result, dict, "return value type of query() should be dict"
            )
            self.assertIsInstance(
                result[list(result.keys())[0]],
                list,
                "from query() returned dict should have lists as its values",
            )
            self.assertIsInstance(
                result[list(result.keys())[0]][0],
                int,
                "from query() returned lists in dict should have an integer value on index 0",
            )
            self.assertIsInstance(
                result[list(result.keys())[0]][1],
                dict,
                "from query() returned lists in dict should have an dict value on index 1",
            )


if __name__ == "__main__":
    unittest.main()
