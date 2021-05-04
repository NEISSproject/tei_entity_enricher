import os
import re
import json
import requests

class FileReader:
    def __init__(self, filepath = None, origin = None, internal_call = False, show_printmessages = True):
        self.filepath = filepath
        self.origin = origin
        self.internal_call = internal_call
        self.show_printmessages = show_printmessages
    def loadfile_json(self):
        if (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    if (os.stat(self.filepath).st_size == 0):
                        #check if file exists and is empty
                        imported_data = "empty"
                    else:
                        imported_data = json.load(loaded_file)
                return imported_data
            except FileNotFoundError:
                if (self.internal_call == False):
                    print("error: file not found") if self.show_printmessages else None
                return None
        elif (self.origin == "web"):
            try:
                response = requests.get(self.filepath)
                imported_data = response.json()
                return imported_data
            except ValueError:
                print("error: file not found or bad format") if self.show_printmessages else None
                return None
        else:
            print("internal error: FileReader.origin not defined") if self.show_printmessages else None
            return False
    def loadfile_beacon(self):
        if (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    return loaded_file.read()
            except FileNotFoundError:
                print("error: file not found") if self.show_printmessages else None
                return None
        elif (self.origin == "web"):
            try:
                response = requests.get(self.filepath)
                loaded_file = response.text
                return loaded_file
            except:
                print("error: couldn't get data due to connection or filepath issue") if self.show_printmessages else None
                return None
        else:
            print("internal error: FileReader.origin not defined") if self.show_printmessages else None
            return False

class Cache:
    def __init__(self, data = None, show_printmessages = True):
        self.data = data
        self.show_printmessages = show_printmessages
    def print_cache(self):
        print(self.data) if self.show_printmessages else None
        return 0
    def check_for_redundancy(self, gnd, category, value):
        #redundancy check, used to compare existing files with cache data concerning gnd number and a category value:
        #example: is a gnd or a name of self.data already present in a file?
        #function can also be used as search routine for values in self.data
        gnd_is_redundant = False
        value_is_redundant = False
        for key in self.data:
            if (key == gnd):
                gnd_is_redundant = True
            if (self.data[key][category] == value):
                value_is_redundant = True
        return gnd_is_redundant, value_is_redundant
    def check_json_structure(self):
        #check json file structure in case of merging Cache.data with an already existing json-file in FileWriter.write() function
        if type(self.data) == dict:
            for key in self.data:
                if type(self.data[key]) == dict:
                    pass
                else:
                    return False
            return True
        else:
            return False
    def check_beacon_prefix_statement(self):
        regex_prefix_line = re.compile("#PREFIX:\s+http:\/\/d-nb.info\/gnd\/")
        regex_meta_lines = re.compile("^#")
        found = False
        lines = self.data.split("\n")
        for line in lines:
            if re.search(regex_meta_lines, line) != None:
                if (re.search(regex_prefix_line, line) != None):
                    found = True
                    break
            else:
                continue
        return found
    def get_gndids_of_beacon_file(self):
        if self.check_beacon_prefix_statement() == True:
            regex_gndid = re.compile("^.{9,10}(?=\|)")
            lines = self.data.split("\n")
            result_list = []
            for line in lines:
                if re.search(regex_gndid, line) != None:
                    result_list.append(re.search(regex_gndid, line).group(0))
            print("in beacon found gndids: {}\ndata: {}".format(len(result_list), result_list)) if self.show_printmessages else None
            return result_list
        else:
            print("error: loaded beacon-file doesn't refer to gnd data or is corrupted") if self.show_printmessages else None
            return None
    def get_items_with_specific_value_in_a_category(self, category, value, mode = "dict"):
        #get filtered cache.data-version returned as a reduced dict or returned as a list of gnd numbers of entities, whose categorys value matches the filter value
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
            print("Cache.get_items_with_specific_value_in_a_category() error: no valid mode parameter has been passed to function") if self.show_printmessages else None
            return None
   
class FileWriter:
    def __init__(self, data = None, filepath = None, show_printmessages = True):
        self.data = data
        self.filepath = filepath
        self.show_printmessages = show_printmessages
    def writefile(self, do_if_file_exists = "cancel"):
        #local definitions for a sort of switch-statement, based on dict "do_if_file_exists_switch"
        def do_if_file_exists_cancel():
            print("file already exists: cancel writing process") if self.show_printmessages else None
            return False
        def do_if_file_exists_replace():
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists: file successfully overwritten") if self.show_printmessages else None
            return True
        def do_if_file_exists_merge():
            if already_existing_file_cache.check_json_structure() == False:
                #if already existing file doesn't match json-schema, tested by check_json_structure(), then cancel writing process
                print("file already exists: couldn't merge files due to incompatibility issue") if self.show_printmessages else None
                return False
            else:
                #if one of the new gnd-ids or name-strings exists also in the already existing file, then cancel writing process
                for key in self.data:
                    redundancy_check_result = already_existing_file_cache.check_for_redundancy(key, "name", self.data[key]["name"])
                    if any(redundancy_check_result):
                        print("file already exists: couldn't merge files due to redundancy issue") if self.show_printmessages else None
                        return False
                #merge new data with data from the already existing file and overwrite it
                already_existing_file_cache.data.update(self.data)
                with open(self.filepath, "w") as file:
                    json.dump(already_existing_file_cache.data, file, indent="\t")
                print("file already exists: files successfully merged") if self.show_printmessages else None
                return True
        do_if_file_exists_switch = {
            "cancel": do_if_file_exists_cancel,
            "replace": do_if_file_exists_replace,
            "merge": do_if_file_exists_merge
        }
        #check for existance of a file with the same name as self.filepath using an instance of FileReader
        already_existing_file = FileReader(self.filepath, "local", True)
        already_existing_file_cache = Cache(already_existing_file.loadfile_json())
        if (already_existing_file_cache.data == None):
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("new file {} successfully created".format(self.filepath)) if self.show_printmessages else None
            return True
        elif (already_existing_file_cache.data == "empty"):
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists, but was empty: file successfully written") if self.show_printmessages else None
            return True
        elif (already_existing_file_cache.data == False):
            print("internal error: cancel writing process") if self.show_printmessages else None
            return False
        else:
            #switch-statement depending on do_if_file_exists-parameter, in case a file with the same name as self.filepath aleady exists and is not empty
            returnvalue = do_if_file_exists_switch.get(do_if_file_exists)()
            return returnvalue