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
        return [Connector(gndlist, apiindex, False, False) for apiindex in [0, 1]]

    def test_init(self):
        for con in self.get_connectors():
            self.assertIsInstance(con, Connector, "variable con should refer to an instance of Connector class")
            self.assertEqual(type(con.apilist[con.apiindex]), dict, "entry of apilist should be of type dict")
            self.assertIn("name", con.apilist[0], "first entry of apilist should have key 'name'")
            if con.connection_established == False:
                self.assertTrue(con.connectivitycheck_single(0), "single connectivity check should has passed: response status should be 200 and response.json() should has been successfully executed")
    def test_print_url(self):
        for con in self.get_connectors():
            self.assertEqual(con.print_complete_url(), 0, "print_complete_url() should return 0")
    def test_return_url(self):
        for con in self.get_connectors():
            self.assertEqual(con.return_complete_url(), con.apilist[con.apiindex]["baseUrl"].format(con.gnd[0]), "return_complete_url() should return a string constructed of 'baseUrl' value (first object in apilist) and gnd '118629662'")
    def test_get_raw_json(self):
        for con in self.get_connectors():
            response = con.get_gnd_data()
            response_keys = list(response.keys())
            err_msg = "get_gnd_data() should return a dict with three keys and a dict as their values"
            self.assertEqual(type(response), dict, err_msg)
            self.assertEqual(len(response), 3, err_msg)
            self.assertEqual(type(response[response_keys[0]]), dict, err_msg)
            self.assertEqual(type(response[response_keys[1]]), dict, err_msg)
            self.assertEqual(type(response[response_keys[2]]), dict, err_msg)
    def test_get_filtered_json(self):
        for con in self.get_connectors():
            response = con.get_gnd_data("base")
            response_keys = list(response.keys())
            basealiases = list(con.apilist[con.apiindex]["baseAliases"].keys())
            err_msg_base_datatype = "get_gnd_data('base') should return a dict with three keys and a dict as their values"
            err_msg_base_keys = "get_gnd_data('base') should return a dict with three keys and a dict as their value, which has a key {} as part of the baseAliases defined in apilist"
            self.assertEqual(type(response), dict, err_msg_base_datatype)
            self.assertEqual(len(response), 3, err_msg_base_datatype)
            self.assertEqual(type(response[response_keys[0]]), dict, err_msg_base_datatype)
            self.assertEqual(type(response[response_keys[1]]), dict, err_msg_base_datatype)
            self.assertEqual(type(response[response_keys[2]]), dict, err_msg_base_datatype)
            for basealias in basealiases:
                self.assertIn(basealias, response[response_keys[0]], err_msg_base_keys.format(basealias))
                self.assertIn(basealias, response[response_keys[1]], err_msg_base_keys.format(basealias))
                self.assertIn(basealias, response[response_keys[2]], err_msg_base_keys.format(basealias))

if __name__ == '__main__':
    unittest.main()