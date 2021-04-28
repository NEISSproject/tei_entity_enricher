import json
import os
import re

import requests


class FileReader:
    def __init__(self, filepath=None, origin=None, internalCall=False, showPrintMessages=True):
        self.filepath = filepath
        self.origin = origin
        self.internalCall = internalCall
        self.showPrintMessages = showPrintMessages

    def loadfile_json(self):
        if (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    if (os.stat(self.filepath).st_size == 0):
                        # check if file exists but is empty
                        imported_data = "empty"
                    else:
                        imported_data = json.load(loaded_file)
                return imported_data
            except FileNotFoundError:
                if (self.internalCall == False):
                    print("error: file not found") if self.showPrintMessages else print("")
                return None
        elif (self.origin == "web"):
            try:
                response = requests.get(self.filepath)
                imported_data = response.json()
                return imported_data
            except ValueError:
                print("error: file not found or bad format") if self.showPrintMessages else print("")
                return None
        else:
            print("internal error: Filereader.origin not defined") if self.showPrintMessages else print("")
            return False

    def loadfile_beacon(self):
        if (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    return loaded_file
            except FileNotFoundError:
                print("error: file not found") if self.showPrintMessages else print("")
                return None
        elif (self.origin == "web"):
            try:
                response = requests.get(self.filepath)
                loaded_file = response.text
                return loaded_file
            except:
                print(
                    "error: couldn't get data due to connection or filepath issue") if self.showPrintMessages else print(
                    "")
                return None
        else:
            print("internal error: Filereader.origin not defined") if self.showPrintMessages else print("")
            return False


class FileWriter:
    def __init__(self, data=None, filepath=None, show_print_messages=True):
        self.data = data
        self.filepath = filepath
        self.showPrintMessages = show_print_messages

    def writefile(self, do_if_file_exists="cancel"):
        # local definitions for a sort of switch-statement, based on dict "doIfFileExists_switch"
        def do_if_file_exists_cancel():
            print("file already exists: cancel writing process") if self.showPrintMessages else print("")
            return False

        def doIfFileExists_replace():
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists: file successfully overwritten") if self.showPrintMessages else print("")
            return True

        def doIfFileExists_merge():
            if (already_existing_file_cache.check_json_structure() == False):
                # if already existing file doesn't match json-schema, tested by check_json_structure(), then cancel writing process
                print(
                    "file already exists: couldn't merge files due to incompatibility issue") if self.showPrintMessages else print(
                    "")
                return False
            else:
                # if one of the new gnd-ids or name-strings exists also in the already existing file, then cancel writing process
                for key in self.data:
                    _x = already_existing_file_cache.check_for_redundancy(key, "name", self.data[key]["name"])
                    if (any(_x)):
                        print(
                            "file already exists: couldn't merge files due to redundancy issue") if self.showPrintMessages else print(
                            "")
                        return False
                # merge new data with data from the already existing file and overwrite it
                already_existing_file_cache.data.update(self.data)
                with open(self.filepath, "w") as file:
                    json.dump(already_existing_file_cache.data, file, indent="\t")
                print("file already exists: files successfully merged") if self.showPrintMessages else print("")
                return True

        doIfFileExists_switch = {
            "cancel": do_if_file_exists_cancel,
            "replace": doIfFileExists_replace,
            "merge": doIfFileExists_merge
        }
        # check for existance of a file with the same name as self.filepath using an instance of Filereader
        already_existing_file = FileReader(self.filepath, "local", True)
        already_existing_file_cache = Cache(already_existing_file.loadfile_json())
        if (already_existing_file_cache.data == None):
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("new file {} successfully created".format(self.filepath)) if self.showPrintMessages else print("")
            return True
        elif (already_existing_file_cache.data == "empty"):
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists, but was empty: file successfully written") if self.showPrintMessages else print(
                "")
            return True
        elif (already_existing_file_cache.data == False):
            print("internal error: cancel writing process") if self.showPrintMessages else print("")
            return False
        else:
            # switch-statement depending on doIfFileExists-parameter, in case a file with the same name as self.filepath aleady exists and is not empty
            returnvalue = doIfFileExists_switch.get(do_if_file_exists)()
            return returnvalue


class Cache:
    def __init__(self, data=None, showPrintMessages=True):
        self.data = data
        self.showPrintMessages = showPrintMessages

    def print_cache(self):
        print(self.data) if self.showPrintMessages else print("")

    # redundancy check, used to compare existing files with cache data concerning gnd number and a category value:
    # example: is a gnd or a name of self.data already present in a file?
    # function can also be used as search routine for values in self.data
    def check_for_redundancy(self, gnd, category, value):
        gnd_is_redundant = False
        value_is_redundant = False
        for key in self.data:
            if (key == gnd):
                gnd_is_redundant = True
            if (self.data[key][category] == value):
                value_is_redundant = True
        return gnd_is_redundant, value_is_redundant

    def check_json_structure(self, custom_test_schema=None):
        # todo: write it (check, if self.data corresponds to json-file schema or custom_test_schema)
        # input: dict
        # output: boolean
        if custom_test_schema is not None:
            pass
        else:
            pass
        # wip: just temporary return clause
        return True

    def check_beacon_prefix_statement(self):
        regex_prefix_line = re.compile("#PREFIX:\s+http:\/\/d-nb.info\/gnd\/")
        regex_meta_lines = re.compile("^#")
        found = False
        lines = self.data.split("\n")
        for line in lines:
            if (re.search(regex_meta_lines, line) != None):
                if (re.search(regex_prefix_line, line) != None):
                    found = True
            else:
                break
        return found

    def get_gndids_of_beacon_file(self):
        if (self.check_beacon_prefix_statement() == True):
            regex_gndid = re.compile("^.{9,10}(?=\|)")
            lines = self.data.split("\n")
            result_list = []
            for line in lines:
                if (re.search(regex_gndid, line) != None):
                    result_list.append(re.search(regex_gndid, line).group(0))
            print("in beacon found gndids: {}\ndata: {}".format(len(result_list),
                                                                result_list)) if self.showPrintMessages else print("")
            return result_list
        else:
            print(
                "error: loaded beacon-file doesn't refer to gnd data or is corrupted") if self.showPrintMessages else print(
                "")

    def get_items_with_specific_value_in_a_category(self, category, value, mode="dict"):
        # get filtered cache.data-version returned as a reduced dict or returned as a list of gnd numbers of entities, whose categorys value matches the filter value
        if mode == "dict":
            result = {}
            for gnd in self.data:
                if self.data[gnd][category] == value:
                    result[gnd] = self.data[gnd]
            return result
        elif mode == "list":
            result = []
            for gnd in self.data:
                if self.data[gnd][category] == value:
                    result.append(self.data[gnd])
            return result
        else:
            print(
                "cache.get_items_with_specific_value_in_a_category() error: no valid mode parameter has been passed to function") if self.showPrintMessages else print(
                "")
            return None
