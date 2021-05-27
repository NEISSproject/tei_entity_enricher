import os
from typing import Union, List
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter
from tei_entity_enricher.util.helper import local_save_path, makedir_if_necessary

class GndConnector:
    def __init__(self, \
                 gnd_id: Union[str, List[str], None] = None, \
                 apiindex: int = 0, \
                 check_connectivity: bool = True, \
                 show_printmessages: bool = True) \
                 -> None:
        """establishes connection to api, from which norm data for entities of Deutsche Nationalbibliothek´s database is retrieved,
        loaded data can be passed to an instance of Cache class for further processing or FileWriter class to save it

        gnd_id: gnd id number(s)
        apiindex: index of selected api in list defined in self.apilist
        check_connectivity: execute connectivity check in __init__() or not (see connectivitycheck_loop())
        show_printmessages: show class internal printmessages on runtime or not

        apilist_filepath: path to apilist config file
        apilist: list of dicts as configuration data set, defining api`s url and aliases for filtering purposes (see get_gnd_data())
        connection_established: data from an api has already been received or not
        remaining_apis_to_check: list of apiindex values, which have not been checked yet in connectivitycheck_loop()"""
        print("initializing GndConnector..") if show_printmessages else None
        self.show_printmessages: bool = show_printmessages
        self.gnd_id: Union[str, List[str]] = gnd_id
        self.apiindex: int = apiindex
        self.apilist_filepath: str = os.path.join(local_save_path, "config", "postprocessing", "gnd_apilist.json")
        self.apilist: Union[dict, None] = FileReader(self.apilist_filepath, "local", True).loadfile_json()
        if self.apilist is None:
            print("GndConnector: could not find gnd_apilist.json in config dir. creating file with default settings...") if self.show_printmessages else None
            self.apilist: List[dict] = [
                {
                    "name": "culturegraph",
                    "baseUrl": "https://hub.culturegraph.org/entityfacts/{}",
                    "baseAliases": {
                        "type": ["@type", "str", "categorial", {"person": "person", "organisation": "organisation", "place": "place"}],
                        "name": ["preferredName", "str", "nominal"],
                        "furtherNames": ["variantName", ["str"], "nominal"],
                        "sameAs": ["sameAs", [{"@id": "str"}], "nominal"],
                        "pseudonyms": ["pseudonym", [{"preferredName": "str"}], "nominal"]
                    },
                    "personAliases": {},
                    "placeAliases": {},
                    "organizationAliases": {}
                },
                {
                    "name": "lobid",
                    "baseUrl": "http://lobid.org/gnd/{}",
                    "baseAliases": {
                        "type": ["type", ["str"], "categorial", {"person": "Person", "organisation": "CorporateBody", "place": "PlaceOrGeographicName"}],
                        "name": ["preferredName", "str", "nominal"],
                        "furtherNames": ["variantName", ["str"], "nominal"],
                        "sameAs": ["sameAs", [{"id": "str"}], "nominal"],
                        "pseudonyms": ["variantNameEntityForThePerson", [{"forename": ["str"], "surname": ["str"]}], "nominal"]
                    },
                    "personAliases": {},
                    "placeAliases": {},
                    "organizationAliases": {}
                }
            ]
            self.apiindex: int = 0
            makedir_if_necessary(os.path.dirname(self.apilist_filepath))
            FileWriter(self.apilist, self.apilist_filepath).writefile_json()
        self.check_connectivity: bool = check_connectivity
        self.connection_established: bool = False
        self.remaining_apis_to_check: list = [i for i,_ in enumerate(self.apilist)]
        if self.check_connectivity == True:
            self.connectivitycheck_loop()
        else:
            print("GndConnector: initialization has been done without connectivity check.") if self.show_printmessages else None
    def connectivitycheck_single(self, \
                                 index_to_test: int, \
                                 gnd_id_to_test: str = "118540238") \
                                 -> bool:
        """auxiliary method of connectivitycheck_loop(),
        checks a single api`s response status code and if response data type is json,
        preset gnd_id_to_test value refers to Goethe"""
        try:
            result: dict = FileReader(self.apilist[index_to_test]["baseUrl"].format(gnd_id_to_test), "web", True, self.show_printmessages)
        except:
            return False
        if result != None and result != False:
            return True
        return False
    def connectivitycheck_loop(self) -> int:
        """recursive connectivity check, checking every single api in self.apilist (ascending)
        and setting self.apiindex to the value of those api, which is first to pass the check successfully.
        returns 0 or -1 for unittest purposes"""
        if self.check_connectivity == False:
            self.check_connectivity == True
        if len(self.remaining_apis_to_check) > 0:
            if self.connectivitycheck_single(self.remaining_apis_to_check[0]) == True:
                print(f"GndConnector: connectivity check passed, connection to {self.apilist[self.remaining_apis_to_check[0]]['name']} api established.") if self.show_printmessages else None
                self.apiindex = self.remaining_apis_to_check[0]
                self.remaining_apis_to_check = [i for i,_ in enumerate(self.apilist)]
                self.connection_established = True
                return 0
            else:
                print(f"GndConnector connectivity check: {self.apilist[self.remaining_apis_to_check[0]]['name']} api is currently not responding as expected. checking for alternatives...") if self.show_printmessages else None
                self.remaining_apis_to_check.remove(self.remaining_apis_to_check[0])
                self.connectivitycheck_loop()
        else:
            print("GndConnector connectivity check error: none of the listed apis is responding as expected.") if self.show_printmessages else None
            return -1
    def print_complete_url(self, \
                           index: int = 0) \
                           -> int:
        """print baseUrl string of the currently selected api defined in self.apilist,
        formatted with a gnd id number of self.gnd_id (list or str) selected by index value.
        returns 0 or -1 for unittest purposes"""
        if self.apiindex not in [i for i,_ in enumerate(self.apilist)]:
            print("GndConnector print_complete_url() error: apiindex is not defined correctly. using default api...") if self.show_printmessages else None
            self.apiindex = 0
        if self.gnd_id is not None:
            if type(self.gnd_id) == str:
                print(f"GndConnector complete URL: {self.apilist[self.apiindex]['baseUrl'].format(self.gnd_id)}") if self.show_printmessages else None
            elif type(self.gnd_id) == list:
                print(f"GndConnector complete URL of gnd id number {index + 1} in passed gnd id list: {self.apilist[self.apiindex]['baseUrl'].format(self.gnd_id[index])}") if self.show_printmessages else None
            return 0
        else:
            print("GndConnector error in print_complete_url(): no gnd id number has been passed to connector object yet.") if self.show_printmessages else None
            return -1
    def return_complete_url(self, \
                            index: int = 0) \
                            -> Union[str, None]:
        """return baseUrl string of the currently selected api defined in self.apilist,
        formatted with a gnd id number of self.gnd_id (list or str) selected by index value"""
        if self.apiindex not in [i for i,_ in enumerate(self.apilist)]:
            print("GndConnector return_complete_url() error: apiindex is not defined correctly. using default api...") if self.show_printmessages else None
            self.apiindex = 0
        if self.gnd_id is not None:
            if type(self.gnd_id) == str:
                return self.apilist[self.apiindex]["baseUrl"].format(self.gnd_id)
            elif type(self.gnd_id) == list:
                return self.apilist[self.apiindex]["baseUrl"].format(self.gnd_id[index])
        else:
            print("GndConnector error in return_complete_url(): no gnd id number has been passed to connector object yet.") if self.show_printmessages else None
            return None
    def get_gnd_data(self, \
                     data_selection: Union[str, List[str], None] = None) \
                     -> Union[dict, None]:
        """method to receive data from api with the possibility to filter results.
        a dict is created, having gnd id numbers as keys and filtered or unfiltered response json data as values"""
        if self.check_connectivity == False:
            print(f"GndConnector note: connections to apis have not been checked yet. to do so manually execute connectivitycheck_loop() method of the current connector object. continuing attempt to receive gnd data from {self.apilist[self.apiindex]['name']} api...") if self.show_printmessages else None
        elif self.connection_established == False:
            print("GndConnector connectivity error: after connectivity check no connection could has been established to any of the available apis. gnd data queries can not be executed at the moment.") if self.show_printmessages else None
            return None
        result = {}
        if type(self.gnd_id) == str:
            _temp_data = {}
            try:
                filereader = FileReader(self.return_complete_url(), "web", True, True)
                _temp_data = filereader.loadfile_json()
            except:
                print("GndConnector connectivity error in get_gnd_data() method: could not load resource from api as expected.") if self.show_printmessages else None
                return None
            self.connection_established = True
            if _temp_data != None and _temp_data != False:
                result[self.gnd_id] = _temp_data
                print(f"GndConnector get_gnd_data() status: data for gnd id {self.gnd_id} received.") if self.show_printmessages else None
            else:
                print(f"GndConnector get_gnd_data() status: for gnd id {self.gnd_id} no data could be delivered by api") if self.show_printmessages else None
                return None
        elif type(self.gnd_id) == list:
            for index, gnd in enumerate(self.gnd_id):
                _temp_data = {}
                try:
                    filereader = FileReader(self.return_complete_url(index), "web", True, True)
                    _temp_data = filereader.loadfile_json()
                except:
                    print("GndConnector connectivity error in get_gnd_data() method: could not load resource from api as expected.") if self.show_printmessages else None
                    return None
                if _temp_data != None and _temp_data != False:
                    result[gnd] = _temp_data
                    print(f"GndConnector get_gnd_data() status: gnd id {index + 1} ({gnd}) of {len(self.gnd_id)} processed") if self.show_printmessages else None
                else:
                    print(f"GndConnector get_gnd_data() status: for gnd id {index + 1} ({gnd}) of {len(self.gnd_id)} no data could be delivered by api") if self.show_printmessages else None
            self.connection_established = True
        # filtering: build new dict with selected values, which should be returned (base mode = all base aliases from apilist definition. list mode = select specific aliases from base set)
        # defining sub method for filtering
        def filter_received_data(gnd_id: str, \
                                 mode: Union[str, List[str]]) \
                                 -> dict:
            """sub method, which extracts the key-value pairs from the raw data received from api for one gnd id number and renames the keys and/or values.
            alias definitions in self.apilist are used for this filtering process:
            the keys of 'baseAliases' dict define the new key names, their value list denotates (in order of the list)
                1. the original key name,
                2. the original value type (python-wise: i.e. 'str' or '[str]'),
                3. the original value type (logic-wise: 'categorial' or 'nominal'),
                4. a categorization dict, if the original value type logic-wise is 'categorial':
                    it delivers mapping information to assign a category (defined keys of this mapping dict) based on specific values (defined in the values of this mapping dict) found in raw data,
                    example 1: using culturegraph api the value of the base category 'type' is assigned to 'person', if the raw data json object has a key '@type' with the value 'person' of type str,
                    example 2: using lobid api the value of the base category 'type' is assigned to 'person', if the raw data json object has a key 'type' with a list as a value, which has itself a value 'Person' of type str in it,
            mode parameter accepts str 'base' (all base aliases will be extracted) or a list of str (specific aliases will be extracted)"""
            # todo: handle additional alias definition sets in gnd_apilist.json by user
            #   category_sets = {'base': [list(self.apilist[self.apiindex]["baseAliases"].keys()), 'baseAliases'],
            #                    'custom': [list(self.apilist[self.apiindex]["custom"].keys()), 'custom']
            #                   }
            #   selected_categories_list = category_sets.get(mode)[0] if type(mode) == str else mode
            #   selected_categories_alias = category_sets.get(mode)[1] if type(mode) == str else 'baseAliases'
            #       => allow parsing a list of categories to get_gnd_data() only if they are defined in baseAlias set?
            base_categories = list(self.apilist[self.apiindex]["baseAliases"].keys())
            selected_categories = base_categories if mode == "base" else mode
            selected_categories_data = {}
            for category in selected_categories:
                _temp_data = []
                try:
                    _temp_data = result[gnd_id][self.apilist[self.apiindex]["baseAliases"][category][0]]
                except KeyError:
                    _temp_data = []
                    print(f"GndConnector get_gnd_data() filtering note: could not find {category} information for {gnd_id} in raw data. continuing processing...") if self.show_printmessages else None
                #handling of categorical data types
                if len(_temp_data) > 0 and self.apilist[self.apiindex]["baseAliases"][category][2] == "categorial" and type(self.apilist[self.apiindex]["baseAliases"][category][3] == dict):
                    _temp_category_data_form = self.apilist[self.apiindex]["baseAliases"][category][1]
                    _temp_categorial_values = self.apilist[self.apiindex]["baseAliases"][category][3]
                    #change found categorial string to selfdefined string (i.e. 'Person' to 'person')
                    if type(_temp_category_data_form) == str:
                        for _type in _temp_categorial_values:
                            if _temp_data == _temp_categorial_values[_type]:
                                _temp_data = _type
                    #replace found categorial list with selfdefined string (i.e. ['Person', 'PoliticalLeader'] to 'person')
                    elif type(_temp_category_data_form) == list:
                        for _type in _temp_categorial_values:
                            if _temp_categorial_values[_type] in _temp_data:
                                _temp_data = _type
                selected_categories_data[category] = _temp_data
            return selected_categories_data
        #executing sub method for filtering
        if data_selection is not None:
            if type(self.gnd_id) == str:
                _new_dict = {list(result.keys())[0]: filter_received_data(self.gnd_id, data_selection)}
            elif type(self.gnd_id) == list:
                _new_dict = {}
                for key in result:
                    _new_dict[key] = filter_received_data(key, data_selection)
            result = _new_dict
        return result