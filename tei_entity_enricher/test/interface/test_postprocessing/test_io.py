import unittest
import tempfile
import os
from tei_entity_enricher.interface.postprocessing.io import (
    FileReader,
    FileWriter,
    Cache,
)
from tei_entity_enricher.util.helper import module_path


class TestPostprocessingIo(unittest.TestCase):
    # auxiliaries
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()  # use this dir for tests

    def tearDown(self):
        self.tempdir.cleanup()  # remove temp dir after all tests of this class are done

    def get_FileReaders(self):
        return [
            FileReader(
                "http://www.andreas-praefcke.de/temp/BEACON-GND-Bern.txt",
                "web",
                False,
                False,
            ),
            FileReader(
                os.path.join(module_path, "util", "beacon_file_for_tests.txt"),
                "local",
                False,
                False,
            ),
            FileReader("http://lobid.org/gnd/1105592812.json", "web", False, False),
            FileReader(
                os.path.join(module_path, "util", "json_file_for_tests.json"),
                "local",
                False,
                False,
            ),
        ]

    # tests
    def test_FileReader_init(self):
        for fr in self.get_FileReaders():
            self.assertIsInstance(
                fr,
                FileReader,
                "variable fr should refer to an instance of FileReader class",
            )

    def test_FileReader_loadfile_json(self):
        for fr in self.get_FileReaders():
            if ".json" in fr.filepath:
                self.assertNotEqual(
                    fr.loadfile_json(), None, "loadfile_json() should not return None"
                )

    def test_FileReader_loadfile_beacon(self):
        for fr in self.get_FileReaders():
            if ".txt" in fr.filepath:
                self.assertNotEqual(
                    fr.loadfile_beacon(),
                    None,
                    "loadfile_beacon() should not return None",
                )

    def test_Cache_init(self):
        for fr in self.get_FileReaders():
            if ".json" in fr.filepath:
                c = Cache(fr.loadfile_json(), False)
                self.assertEqual(c.print_cache(), 0, "print_cache() should return 0")
            if ".txt" in fr.filepath:
                c = Cache(fr.loadfile_beacon(), False)
                self.assertEqual(c.print_cache(), 0, "print_cache() should return 0")

    def test_Cache_redundancy_check(self):
        test_dict = {
            "123": {"name": "Max Mustermann"},
            "456": {"name": "Maxine Musterfrau"},
        }
        c = Cache(test_dict, False)
        self.assertTrue(
            any(c.check_for_redundancy("123", "name", "Maxine Mustermann")),
            "any(check_for_redundancy()) should return True",
        )
        self.assertTrue(
            any(c.check_for_redundancy("789", "name", "Maxine Musterfrau")),
            "any(check_for_redundancy()) should return True",
        )
        self.assertFalse(
            any(c.check_for_redundancy("789", "name", "Maxine Mustermann")),
            "any(check_for_redundancy()) should return False",
        )

    def test_Cache_json_stucture_check(self):
        test_dict_true = {
            "123": {"name": "Max Mustermann"},
            "456": {"name": "Maxine Musterfrau"},
        }
        test_dict_false_object = ["123", "Max Mustermann", "456", "Maxine Musterfrau"]
        test_dict_false_value = {
            "123": ["name", "Max Mustermann"],
            "456": {"name": "Maxine Musterfrau"},
        }
        self.assertTrue(
            Cache(test_dict_true, False).check_json_structure(),
            "check_json_structure() should return True",
        )
        self.assertFalse(
            Cache(test_dict_false_object, False).check_json_structure(),
            "check_json_structure() should return False",
        )
        self.assertFalse(
            Cache(test_dict_false_value, False).check_json_structure(),
            "check_json_structure() should return False",
        )

    def test_Cache_beacon_praefix_check(self):
        for fr in self.get_FileReaders():
            if ".txt" in fr.filepath:
                c = Cache(fr.loadfile_beacon(), False)
                self.assertTrue(
                    c.check_beacon_prefix_statement(),
                    "check_beacon_prefix_statement() should return True",
                )

    def test_Cache_get_gnd_ids_of_beacon_file(self):
        for fr in self.get_FileReaders():
            if ".txt" in fr.filepath:
                c = Cache(fr.loadfile_beacon(), False)
                result = c.get_gnd_ids_of_beacon_file()
                self.assertEqual(
                    type(result),
                    list,
                    "get_gnd_ids_of_beacon_file() should return a list",
                )
                self.assertGreater(
                    len(result),
                    0,
                    "get_gnd_ids_of_beacon_file() should return a list with elements in it",
                )

    def test_Cache_get_items_with_specific_value_in_a_category(self):
        test_dict = {
            "123": {"name": "123", "type": "a"},
            "456": {"name": "456", "type": "b"},
            "789": {"name": "789", "type": "a"},
        }
        c = Cache(test_dict, False)
        result = c.get_items_with_specific_value_in_a_category("type", "a")
        self.assertEqual(
            len(result),
            2,
            "get_items_with_specific_value_in_a_category() should return a dict with 2 dicts",
        )
        self.assertEqual(
            result[list(result.keys())[0]]["type"],
            "a",
            "get_items_with_specific_value_in_a_category() should return a dict with 2 dicts, which has a key 'type' with value 'a'",
        )
        self.assertEqual(
            result[list(result.keys())[1]]["type"],
            "a",
            "get_items_with_specific_value_in_a_category() should return a dict with 2 dicts, which has a key 'type' with value 'a'",
        )

    def test_FileWriter_init(self):
        fw = FileWriter(None, None, False)
        self.assertIsInstance(
            fw,
            FileWriter,
            "variable fw should refer to an instance of FileWriter class",
        )

    def test_FileWriter_writefile_json(self):
        test_dict = {
            "123": {"name": "123", "type": "a"},
            "456": {"name": "456", "type": "b"},
            "789": {"name": "789", "type": "a"},
        }
        if os.path.exists(os.path.join(module_path, "util", "testfile.json")):
            print(
                "test_FileWriter_writefile_json(): testfile.json already exists. Delete and continue test? (Y or skip with everything else)"
            )
            answer = input()
            if answer == "Y":
                os.remove(os.path.join(module_path, "util", "testfile.json"))
            else:
                self.skipTest("test_FileWriter_writefile_json(): Test skipped by User")
        fw = FileWriter(
            test_dict, os.path.join(module_path, "util", "testfile.json"), False
        )
        self.assertTrue(
            fw.writefile_json(),
            "writefile_json() should return True, when writing a new file",
        )
        self.assertFalse(
            fw.writefile_json(),
            "writefile_json() should return False, when a file with filepath already exists and writefile_json()s parameter 'do_if_file_exists' is 'cancel'",
        )
        self.assertTrue(
            fw.writefile_json("replace"),
            "writefile_json() should return True, when replacing an existing file and writefile_json()s parameter 'do_if_file_exists' is 'replace'",
        )
        fw.data = {
            "1234": {"name": "1234", "type": "a"},
            "4567": {"name": "4567", "type": "b"},
            "7890": {"name": "7890", "type": "a"},
        }
        self.assertTrue(
            fw.writefile_json("merge"),
            "writefile_json() should return True, when merging data with an existing file and writefile_json()s parameter 'do_if_file_exists' is 'merge'",
        )
        if os.path.exists(os.path.join(module_path, "util", "testfile.json")):
            os.remove(os.path.join(module_path, "util", "testfile.json"))


if __name__ == "__main__":
    unittest.main()
