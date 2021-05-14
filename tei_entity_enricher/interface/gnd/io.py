import os
import re
import json
import requests
from typing import Union, List, Tuple

class FileReader:
    def __init__(self, \
                 filepath: Union[str, None] = None, \
                 origin: Union[str, None] = None, \
                 internal_call: bool = False, \
                 show_printmessages: bool = True):
        """loads json and beacon files from local file system or web source,
        used internally in Connector and FileWriter class and on its own in a beacon file processing pipeline,
        in which gnd id numbers are extracted out of a beacon file, enriched with related information and saved in a json file
        
        filepath: path to file to read
        origin: values can be 'web' or 'local', to determine, whether self.filepath contains an url or a local file path
        internal_call: if FileReader is used internally in Connector or FileWriter class, some error messages will not be printed
        show_printmessages: show class internal printmessages on runtime or not"""
        self.filepath: Union[str, None] = filepath
        self.origin: Union[str, None] = origin
        self.internal_call: bool = internal_call
        self.show_printmessages: bool = show_printmessages
    def loadfile_json(self) -> Union[dict, str, None, bool]:
        """method to load json files, locally or out of the web,
        it returns:
            a json object,
            a string 'empty' (in case a file in self.filepath was found, but is empty),
            None (in case of preceding definition errors)
            or False (in case of file not found error or bad format error)"""
        if (self.filepath == None):
            print("internal error: FileReader.filepath not defined") if self.show_printmessages else None
            return False
        if (self.origin == None):
            print("internal error: FileReader.origin not defined") if self.show_printmessages else None
            return False
        elif (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    if (os.stat(self.filepath).st_size == 0):
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
    def loadfile_beacon(self) -> Union[str, None, bool]:
        """method to load beacon files, locally or out of the web,
        beacon is a file format to list norm data, often used in digital editions
        to offer a list of all entities, which can be found in the edition,
        those beacon file mostly contain only gnd numbers, but no further informations about the listed entities,
        the method can return:
            a json object,
            a string 'empty' (in case a file in self.filepath was found, but is empty),
            None (in case of preceding definition errors)
            or False (in case of file not found error or bad format error)"""
        if (self.filepath == None):
            print("internal error: FileReader.filepath not defined") if self.show_printmessages else None
            return False
        if (self.origin == None):
            print("internal error: FileReader.origin not defined") if self.show_printmessages else None
            return False
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

class Cache:
    def __init__(self, data: Union[str, None] = None, show_printmessages: bool = True):
        """saves data for manipulation processes used in a beacon file processing pipeline,
        
        data: contains data of beacon or json files as a string, delivered by FileReader class
        show_printmessages: show class internal printmessages on runtime or not
        """
        self.data: Union[str, None] = data
        self.show_printmessages: bool = show_printmessages
    def print_cache(self) -> int:
        print(self.data) if self.show_printmessages else None
        return 0
    def check_for_redundancy(self, gnd: str, category: str, value: Union[str, dict, list, bool, None]) -> Tuple[bool, bool]:
        """used to check a dict in self.data for an existing gnd number and value,
        a specific dict structure is presupposed:
        {'gnd1':
            {'gnd1_key1': 'gnd1_val1',
            'gnd1_key2': 'gnd1_val2'},
         'gnd2':
            {'gnd2_key1': 'gnd2_val1',
            'gnd2_key2': 'gnd2_val2'}       
        }
        this check is used in FileWriter class as part
        of a merging process of an existing json file and new json data,
        which should be added to the file:
        if a specific gnd number and a specific value is already present in the file,
        the merging process will be canceled (see FileWriter class for more information)"""
        gnd_is_redundant = False
        value_is_redundant = False
        for key in self.data:
            if (key == gnd):
                gnd_is_redundant = True
            if (self.data[key][category] == value):
                value_is_redundant = True
        return gnd_is_redundant, value_is_redundant
    def check_json_structure(self) -> bool:
        """check json file structure in case of merging self.data
        with an already existing json file in FileWriter class,
        a specific dict structure is presupposed:
        {'gnd1':
            {'gnd1_key1': 'gnd1_val1',
            'gnd1_key2': 'gnd1_val2'},
         'gnd2':
            {'gnd2_key1': 'gnd2_val1',
            'gnd2_key2': 'gnd2_val2'}       
        }"""
        if type(self.data) == dict:
            for key in self.data:
                if type(self.data[key]) == dict:
                    pass
                else:
                    return False
            return True
        else:
            return False
    def check_beacon_prefix_statement(self) -> bool:
        """method to check an imported beacon file, if the listed entities are defined by gnd norm data ids"""
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
    def get_gndids_of_beacon_file(self) -> List[str]:
        """method to get all listed gnd numbers of a beacon file"""
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
    def get_items_with_specific_value_in_a_category(self, category: str, value: str, mode: str = "dict") -> Union[dict, list, bool]:
        """method to filter self.data dict, refering to the existance of a specific value in a category,
        i.e. get all gnd entities, which are of type person,
        parameter 'mode' controls format of the return value"""
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
            return False
   
class FileWriter:
    def __init__(self, data: Union[str, None] = None, filepath: Union[str, None] = None, show_printmessages: bool = True):
        """writes dict conform data into json files
        
        data: contains data of json files as a string, delivered by FileReader or Cache class
        filepath: path to file to write
        show_printmessages: show class internal printmessages on runtime or not"""
        self.data: Union[str, None] = data
        self.filepath: Union[str, None] = filepath
        self.show_printmessages: bool = show_printmessages
    def writefile(self, do_if_file_exists: str = "cancel") -> bool:
        """method to write a new or enrich an existing json file,
        do_if_file_exists parameter controls behavior in case a file in self.filepath already exists,
        there are 3 sub-methods defined for a sort of switch statement"""
        def do_if_file_exists_cancel() -> bool:
            print("file already exists: cancel writing process") if self.show_printmessages else None
            return False
        def do_if_file_exists_replace() -> bool:
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists: file successfully overwritten") if self.show_printmessages else None
            return True
        def do_if_file_exists_merge() -> bool:
            if already_existing_file_cache.check_json_structure() == False:
                print("file already exists: couldn't merge files due to incompatibility issue") if self.show_printmessages else None
                return False
            else:
                for key in self.data:
                    redundancy_check_result = already_existing_file_cache.check_for_redundancy(key, "name", self.data[key]["name"])
                    if any(redundancy_check_result):
                        print("file already exists: couldn't merge files due to redundancy issue") if self.show_printmessages else None
                        return False
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
            returnvalue = do_if_file_exists_switch.get(do_if_file_exists)()
            return returnvalue