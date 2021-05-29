import os
import re
import json
import requests
import csv
from typing import Union, List, Tuple


class FileReader:
    def __init__(
        self,
        filepath: Union[str, None] = None,
        origin: Union[str, None] = None,
        internal_call: bool = False,
        show_printmessages: bool = True,
    ) -> None:
        """loads json, beacon, csv and tsv files from local file system or web source,
        used internally in Connector and FileWriter classes and on its own in a beacon file processing pipeline,
        in which gnd id numbers are extracted out of a beacon file, enriched with related information and saved in a json file

        filepath: path to file to read
        origin: values can be 'web' or 'local', to determine, whether self.filepath contains an url or a local file path
        internal_call: if FileReader is used internally in Connector or FileWriter class, some error messages will not be printed
        show_printmessages: show class internal printmessages on runtime or not

        loadfile_types: dict mapping file extensions to loading methods, can be used from outside to execute the right loading function"""
        self.filepath: Union[str, None] = filepath
        self.origin: Union[str, None] = origin
        self.internal_call: bool = internal_call
        self.show_printmessages: bool = show_printmessages
        self.loadfile_types: dict = {
            ".json": "loadfile_json",
            ".csv": "loadfile_csv",
            ".tsv": "loadfile_tsv",
            ".txt": "loadfile_beacon",
        }

    def loadfile_json(self) -> Union[dict, str, None, bool]:
        """method to load json files, locally or out of the web,
        it returns:
            a json object,
            a string 'empty' (in case a file in self.filepath was found, but is empty),
            None (in case of preceding definition errors)
            or False (in case of file not found error or bad format error)"""
        if self.filepath == None:
            print(
                "FileReader loadfile_json() internal error: FileReader.filepath not defined"
            ) if self.show_printmessages else None
            return False
        if self.origin == None:
            print(
                "FileReader loadfile_json() internal error: FileReader.origin not defined"
            ) if self.show_printmessages else None
            return False
        elif self.origin == "local":
            try:
                with open(self.filepath) as loaded_file:
                    if os.stat(self.filepath).st_size == 0:
                        imported_data = "empty"
                    else:
                        imported_data = json.load(loaded_file)
                return imported_data
            except FileNotFoundError:
                if self.internal_call == False:
                    print("FileReader loadfile_json() error: file not found") if self.show_printmessages else None
                return None
            except json.decoder.JSONDecodeError:
                if self.internal_call == False:
                    print("FileReader loadfile_json() error: bad format") if self.show_printmessages else None
                return None
        elif self.origin == "web":
            try:
                response = requests.get(self.filepath)
                imported_data = response.json()
                response.close()
                return imported_data
            except ValueError:
                print(
                    "FileReader loadfile_json() error: file not found or bad format"
                ) if self.show_printmessages else None
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
        if self.filepath == None:
            print(
                "FileReader loadfile_beacon() internal error: FileReader.filepath not defined"
            ) if self.show_printmessages else None
            return False
        if self.origin == None:
            print(
                "FileReader loadfile_beacon() internal error: FileReader.origin not defined"
            ) if self.show_printmessages else None
            return False
        if self.origin == "local":
            try:
                with open(self.filepath) as loaded_file:
                    return loaded_file.read()
            except FileNotFoundError:
                print("FileReader loadfile_beacon() error: file not found") if self.show_printmessages else None
                return None
        elif self.origin == "web":
            try:
                response = requests.get(self.filepath)
                loaded_file = response.text
                response.close()
                return loaded_file
            except:
                print(
                    "FileReader loadfile_beacon() error: couldn't get data due to connection or filepath issue"
                ) if self.show_printmessages else None
                return None

    def loadfile_csv(
        self, delimiting_character: str = ",", transform_for_entity_library_import: bool = True
    ) -> Union[dict, None, bool]:
        """method to load csv files, locally or out of the web,
        is specialized to be used to add data to entity library;
        the csv file should contain the following key names
        in the first row (order and upper- or lowercase doesnt matter):
        name, type, wikidata_id, gnd_id, furtherNames\0;
        if two furtherNames are provided, the second should be saved in
        a key field named furtherNames\1 and so on;
        delimiter: define character, which delimits the fields in the csv file
        transform_for_entity_library_import: activate data transformation for usecase of importing
        entity data into entity library"""
        if self.filepath == None:
            print(
                "FileReader loadfile_csv() internal error: FileReader.filepath not defined"
            ) if self.show_printmessages else None
            return False
        if self.origin == None:
            print(
                "FileReader loadfile_csv() internal error: FileReader.origin not defined"
            ) if self.show_printmessages else None
            return False
        if self.origin == "local":
            try:
                if transform_for_entity_library_import == True:
                    result = []
                    with open(self.filepath) as loaded_file:
                        csv_reader = csv.DictReader(loaded_file)
                        for row in csv_reader:
                            new_row = {}
                            new_furtherNames = []
                            for key in list(row.keys()):
                                if "furthernames" in key.lower():
                                    new_furtherNames.append(row[key])
                                    continue
                                new_row[key.lower()] = row[key]
                            new_row["furtherNames"] = new_furtherNames
                            result.append(new_row)
                        return result
            except FileNotFoundError:
                print("FileReader loadfile_csv() error: file not found") if self.show_printmessages else None
                return None
        elif self.origin == "web":
            try:
                if transform_for_entity_library_import == True:
                    result = []
                    response = requests.get(self.filepath)
                    loaded_file = response.content.decode("utf-8")
                    csv_reader = csv.DictReader(loaded_file.splitlines(), delimiter=delimiting_character)
                    for row in csv_reader:
                        new_row = {}
                        new_furtherNames = []
                        for key in list(row.keys()):
                            if "furthernames" in key.lower():
                                new_furtherNames.append(row[key])
                                continue
                            new_row[key.lower().strip()] = row[key]
                        new_row["furtherNames"] = new_furtherNames
                        result.append(new_row)
                    response.close()
                    return result
            except:
                print(
                    "FileReader loadfile_csv() error: couldn't get data due to connection or filepath issue"
                ) if self.show_printmessages else None
                return None

    def loadfile_tsv(self) -> Union[str, None, bool]:
        """method to load tsv files, locally or out of the web,
        is used to add data to entity library"""
        pass


class Cache:
    def __init__(self, data: Union[str, None] = None, show_printmessages: bool = True) -> None:
        """saves data for manipulation processes, offers methods for diverse purposes, used in a beacon file processing pipeline and
        EntityLibrary saving process,

        data: contains data of beacon or json files as a string, delivered by FileReader class
        show_printmessages: show class internal printmessages on runtime or not
        """
        self.data: Union[str, None] = data
        self.show_printmessages: bool = show_printmessages

    def print_cache(self) -> int:
        print(self.data)
        return 0

    def check_for_redundancy(
        self,
        usecase: str = None,
        wikidata_id: str = None,
        gnd_id: str = None,
        category: str = None,
        value: Union[str, dict, list, bool, None] = None,
    ) -> Union[Tuple[bool, bool], None]:
        """usecase: GndConnector:
        checks a dict in self.data for an existing gnd id number and value,
        a specific dict structure is presupposed:
        {'gnd_id1':
            {'gnd_id1_key1': 'gnd_id1_val1',
            'gnd_id1_key2': 'gnd_id1_val2'},
         'gnd_id2':
            {'gnd_id2_key1': 'gnd_id2_val1',
            'gnd_id2_key2': 'gnd_id2_val2'}
        }
        usecase: EntityLibrary:
        checks a dict in self.data for an existing wikidata_id and gnd_id,
        a specific dict structure is presupposed:
        [
            {
                'name': 'entityName1',
                'furtherNames': [],
                'type': 'entityType',
                'wikidata_id': 'Q1234',
                'gnd_id': '12345678'
            },
            {
                'name': 'entityName2',
                'furtherNames': [],
                'type': 'entityType',
                'wikidata_id': 'Q12345',
                'gnd_id': '123456789'
            }
        ]
        this check is used in FileWriter class as part
        of a merging process of an existing json file and new json data
        (in the usecases of GndConnector or EntityLibrary),
        which should be added to the file:
        but if a specific gnd id number and a specific value (usecase GndConnector)
        or a specific entity (EntityLibrary) is already present in the file,
        the merging process will be canceled (see FileWriter class)"""
        if usecase == "GndConnector":
            gnd_id_is_redundant = False
            value_is_redundant = False
            for key in self.data:
                if key == gnd_id:
                    gnd_id_is_redundant = True
                if self.data[key][category] == value:
                    value_is_redundant = True
            return gnd_id_is_redundant, value_is_redundant
        elif usecase == "EntityLibrary":
            # todo: write it
            pass
        else:
            print(
                "Cache check_for_redundancy() internal error: No valid usecase value has been passed to function"
            ) if self.show_printmessages else None
            return None

    def check_json_structure(self, usecase: str = "GndConnector") -> Union[bool, None]:
        """check json file structure in case of merging self.data
        with an already existing json file in FileWriter class,
        a specific dict structure is presupposed:
        {'gnd_id1':
            {'gnd_id1_key1': 'gnd_id1_val1',
            'gnd_id1_key2': 'gnd_id1_val2'},
         'gnd_id2':
            {'gnd_id2_key1': 'gnd_id2_val1',
            'gnd_id2_key2': 'gnd_id2_val2'}
        }
        usecase: 'GndConnector' or 'EntityLibrary'"""
        if usecase == "GndConnector":
            if type(self.data) == dict:
                for key in self.data:
                    if type(self.data[key]) != dict:
                        return False
                return True
            else:
                return False
        elif usecase == "EntityLibrary":
            pass
            # todo: write
        else:
            print(
                "Cache check_json_structure() internal error: No valid usecase value passed to function"
            ) if self.show_printmessages else None
            return None

    def check_beacon_prefix_statement(self) -> bool:
        """method to check an imported beacon file, if the listed entities are defined by gnd norm data ids"""
        regex_prefix_line = re.compile("#PREFIX:\s+http:\/\/d-nb.info\/gnd\/")
        regex_meta_lines = re.compile("^#")
        found = False
        lines = self.data.split("\n")
        for line in lines:
            if re.search(regex_meta_lines, line) != None:
                if re.search(regex_prefix_line, line) != None:
                    found = True
                    break
            else:
                continue
        return found

    def get_gnd_ids_of_beacon_file(self) -> List[str]:
        """method to get all listed gnd id numbers from a beacon file"""
        if self.check_beacon_prefix_statement() == True:
            regex_gndid = re.compile("^.{9,10}(?=\|)")
            lines = self.data.split("\n")
            result_list = []
            for line in lines:
                line_search_result = re.search(regex_gndid, line)
                if line_search_result != None:
                    result_list.append(line_search_result.group(0))
            print(
                f"in beacon found gndids: {len(result_list)}\ndata: {result_list}"
            ) if self.show_printmessages else None
            return result_list
        else:
            print(
                "Cache get_gnd_ids_of_beacon_file() error: loaded beacon-file doesn't refer to gnd data or is corrupted"
            ) if self.show_printmessages else None
            return None

    def get_items_with_specific_value_in_a_category(
        self, category: str, value: str, mode: str = "dict"
    ) -> Union[dict, list, bool]:
        """method to filter self.data dict, refering to the existance of a specific value in a category,
        i.e. get all gnd entities, which are of type person,
        parameter 'mode' controls the format of the return value"""
        if mode == "dict":
            result = {}
            for gnd_id in self.data:
                if self.data[gnd_id][category] == value:
                    result[gnd_id] = self.data[gnd_id]
            return result
        elif mode == "list":
            result = []
            for gnd_id in self.data:
                if self.data[gnd_id][category] == value:
                    result.append(self.data[gnd_id])
            return result
        else:
            print(
                "Cache get_items_with_specific_value_in_a_category() internal error: no valid mode parameter has been passed to function"
            ) if self.show_printmessages else None
            return False


class FileWriter:
    def __init__(
        self,
        data: Union[str, None] = None,
        filepath: Union[str, None] = None,
        show_printmessages: bool = True,
    ) -> None:
        """writes data into files

        data: contains data of files as a string, delivered by FileReader or Cache class
        filepath: path to file to write
        show_printmessages: show class internal printmessages on runtime or not

        writefile_types: dict mapping file extensions to writing methods, can be used from outside to execute the right writing function"""
        self.data: Union[str, None] = data
        self.filepath: Union[str, None] = filepath
        self.show_printmessages: bool = show_printmessages
        self.writefile_types: dict = {".json": "writefile_json"}

    def writefile_json(self, do_if_file_exists: str = "cancel", usecase: str = "GndConnector") -> bool:
        """method to write a new or enrich an existing json file,
        do_if_file_exists parameter controls behavior in case a file in self.filepath already exists,
        there are 3 submethods defined for a sort of switch statement, differentiating the 3 cases
        'cancel', 'replace' and 'merge'
        usecase: can be 'GndConnector' 'or 'EntityLibrary'"""

        def do_if_file_exists_cancel() -> bool:
            print(
                "FileWriter writefile_json(): file already exists, cancel writing process"
            ) if self.show_printmessages else None
            return False

        def do_if_file_exists_replace() -> bool:
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print(
                "FileWriter writefile_json(): file already exists, file successfully overwritten"
            ) if self.show_printmessages else None
            return True

        def do_if_file_exists_merge() -> bool:
            if already_existing_file_cache.check_json_structure(usecase) == False:
                print(
                    "FileWriter writefile_json(): file already exists, couldn't merge files due to incompatibility issue"
                ) if self.show_printmessages else None
                return False
            else:
                if usecase == "GndConnector":
                    for key in self.data:
                        redundancy_check_result = already_existing_file_cache.check_for_redundancy(
                            "GndConnector", None, key, "name", self.data[key]["name"]
                        )
                        if any(redundancy_check_result):
                            print(
                                "FileWriter writefile_json(): file already exists, couldn't merge files due to redundancy issue"
                            ) if self.show_printmessages else None
                            return False
                    already_existing_file_cache.data.update(self.data)
                    with open(self.filepath, "w") as file:
                        json.dump(already_existing_file_cache.data, file, indent="\t")
                    print(
                        "FileWriter writefile_json(): file already exists, files successfully merged"
                    ) if self.show_printmessages else None
                    return True
                elif usecase == "EntityLibrary":
                    pass
                    # todo: write
                else:
                    print(
                        "FileWriter writefile_json() internal error: No valid usecase value has been passed to function"
                    ) if self.show_printmessages else None
                    return False

        do_if_file_exists_switch = {
            "cancel": do_if_file_exists_cancel,
            "replace": do_if_file_exists_replace,
            "merge": do_if_file_exists_merge,
        }
        already_existing_file = FileReader(self.filepath, "local", True)
        already_existing_file_cache = Cache(already_existing_file.loadfile_json())
        if already_existing_file_cache.data == None:
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print(
                f"FileWriter writefile_json(): new file {self.filepath} successfully created"
            ) if self.show_printmessages else None
            return True
        elif already_existing_file_cache.data == "empty":
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print(
                "FileWriter writefile_json(): file already exists but was empty, file successfully written"
            ) if self.show_printmessages else None
            return True
        elif already_existing_file_cache.data == False:
            print(
                "FileWriter writefile_json() internal error: cancel writing process"
            ) if self.show_printmessages else None
            return False
        else:
            returnvalue = do_if_file_exists_switch.get(do_if_file_exists)()
            return returnvalue
