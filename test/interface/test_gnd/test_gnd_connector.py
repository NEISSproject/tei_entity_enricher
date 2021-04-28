import unittest
import tempfile

from tei_entity_enricher.interface.gnd.connector import Connector


class TestGNDConnector(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()  # use this dir for tests

    def tearDown(self) -> None:
        self.tempdir.cleanup()  # remove temp dir after all tests of this class are done


    def get_connectors(self):  # not a test (does not start with 'test')
        gndlist = ["118629662", "11855817X", "4015796-9"]
        return [Connector(gndlist, apiindex, False) for apiindex in [0, 1]]

    def test_init_connectors(self):
        print("###############\n1. initializing Connectors\n###############\n\n")
        for connector in self.get_connectors():
            assert connector.print_complete_url() == 0

    def test_get_raw_json(self):
        for connector in self.get_connectors():
            raw_data = connector.get_gnd_data()
            print("raw json data from culturegraph api saved in a dict object with gnd numbers which serve as keys:")
            print(raw_data)
            assert isinstance(raw_data, dict)

    def test_filtered_json(self):
        for connector in self.get_connectors():
            filtered_data = connector.get_gnd_data(["type", "name"])
            print("filtered json data from lobid api saved in a dict object with gnd numbers which serve as keys:")
            print(filtered_data)
            assert isinstance(filtered_data, dict)
            for key in filtered_data:
                print(f"{key}: {filtered_data[key]}")
                assert filtered_data[key], "filtered data should not be emtpty here"

            filter_not_exist = connector.get_gnd_data(["not_a_key_in_the_data"])
            assert isinstance(filter_not_exist, dict)
            for key in filter_not_exist:
                print(f"{key}: {filter_not_exist[key]}")
                assert not filter_not_exist[key], "filtered data must be emtpty here!"


