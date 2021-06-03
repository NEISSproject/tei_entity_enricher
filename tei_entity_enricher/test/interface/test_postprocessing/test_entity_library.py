import unittest
import tempfile
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary

# todo: complete


class TestPostprocessingEntityLibrary(unittest.TestCase):
    # auxiliaries
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()  # use this dir for tests

    def tearDown(self):
        self.tempdir.cleanup()  # remove temp dir after all tests of this class are done

    def get_entity_library(self):
        return [EntityLibrary()]

    # tests
    def test_EntityLibrary_init(self):
        for el in self.get_entity_library():
            self.assertIsInstance(
                el,
                EntityLibrary,
                "variable el should refer to an instance of EntityLibrary class",
            )

    def test_EntityLibrary_load_library(self):
        for el in self.get_entity_library():
            self.assertEqual(type(el.load_library()), bool, "type of loaded library data should be bool")

    def test_EntityLibrary_add_entities(self):
        for el in self.get_entity_library():
            self.assertEqual(
                el.add_entities(
                    [{"name": "Test", "furtherNames": [], "type": "test", "wikidata_id": "Q123", "gnd_id": "123"}]
                ),
                0,
                "an integer with value 0 should be returned because a new entity should has been successfully added to entity library",
            )
            self.assertEqual(
                el.add_entities(
                    [{"name": "Test", "furtherNames": "", "type": "test", "wikidata_id": "", "gnd_id": ""}]
                ),
                -1,
                "an integer with value -1 should be returned because the value of furtherNames has to be of type list",
            )
            self.assertEqual(
                el.add_entities(
                    [{"name": "Test", "furtherNames": [], "type": "test", "wikidata_id": "Q123", "gnd_id": ""}]
                ),
                -1,
                "an integer with value -1 should be returned because the passed wikidata_id is already assigned to an entity in entity library",
            )
            self.assertEqual(
                el.add_entities(
                    [{"name": "Test", "furtherNames": [], "type": "test", "wikidata_id": "", "gnd_id": "123"}]
                ),
                -1,
                "an integer with value -1 should be returned because the passed gnd_id is already assigned to an entity in entity library",
            )
