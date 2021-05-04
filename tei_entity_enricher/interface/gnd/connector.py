import os
import requests
from tei_entity_enricher.interface.gnd.io import FileReader, FileWriter, Cache
from tei_entity_enricher.util.helper import module_path

class Connector:
    def __init__(self, gnd = None, apiindex = 0, check_connectivity = True, show_printmessages = True):
        self.show_printmessages = show_printmessages
        print("initializing connector..") if self.show_printmessages else None
        self.gnd = gnd
        self.apiindex = apiindex
        self.apilist = FileReader(os.path.join(module_path, "util/apilist.json"), "local", True).loadfile_json()
        if self.apilist is None:
            print("connector error: could not find apilist.json. using default settings...") if self.show_printmessages else None
            self.apilist = [
                {
                    "name": "culturegraph",
                    "baseUrl": "https://hub.culturegraph.org/entityfacts/{}",
                    "baseAliases": {
                        "type": ["@type", "str", "categorial", {"person": "person", "organisation": "organisation", "place": "place"}],
                        "name": ["preferredName", "str", "nominal"],
                        "furtherNames": ["variantName", ["str"], "nominal"],
                        "sameAs": ["sameAs", [{"@id": "str"}], "nominal"]
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
                        "sameAs": ["sameAs", [{"id": "str"}], "nominal"]
                    },
                    "personAliases": {},
                    "placeAliases": {},
                    "organizationAliases": {}
                }
            ]
            self.apiindex = 0
        self.check_connectivity = check_connectivity
        self.connection_established = False
        self.remaining_apis_to_check = [i for i,_ in enumerate(self.apilist)]
        if self.check_connectivity == True:
            self.connectivitycheck_loop()
        else:
            print("connector: initialization has been done without connectivity check.") if self.show_printmessages else None
    def connectivitycheck_single(self, index_to_test, gnd_to_test = "118540238"):
        #preset test gnd: Goethe
        response = requests.get(self.apilist[index_to_test]["baseUrl"].format(gnd_to_test))
        if response.status_code == 200:
            try:
                response.json()
            except:
                return False
            return True
        else:
            return False
    def connectivitycheck_loop(self):
        if self.check_connectivity == False:
            self.check_connectivity == True
        if len(self.remaining_apis_to_check) > 0:
            if self.connectivitycheck_single(self.remaining_apis_to_check[0]) == True:
                print("connectivity check passed: connection to {} api established.".format(self.apilist[self.remaining_apis_to_check[0]]["name"])) if self.show_printmessages else None
                self.apiindex = self.remaining_apis_to_check[0]
                self.remaining_apis_to_check = [i for i,_ in enumerate(self.apilist)]
                self.connection_established = True
            else:
                print("connectivity check: {} api is currently not responding as expected. checking for alternatives...".format(self.apilist[self.remaining_apis_to_check[0]]["name"])) if self.show_printmessages else None
                self.remaining_apis_to_check.remove(self.remaining_apis_to_check[0])
                self.connectivitycheck_loop()
        else:
            print("connectivity check error: none of the listed apis is responding as expected.") if self.show_printmessages else None
    def print_complete_url(self, index = 0):
        if self.apiindex not in [i for i,_ in enumerate(self.apilist)]:
            print("connector.print_complete_url() error: apiindex is not defined correctly. using default api...") if self.show_printmessages else None
            self.apiindex = 0
        if self.gnd is not None:
            if type(self.gnd) == str:
                print("connector complete URL: {}".format(self.apilist[self.apiindex]["baseUrl"].format(self.gnd))) if self.show_printmessages else None
            elif type(self.gnd) == list:
                print("connector complete URL of gnd number {} in passed gnd list: {}".format(index + 1, self.apilist[self.apiindex]["baseUrl"].format(self.gnd[index]))) if self.show_printmessages else None
            return 0
        else:
            print("connector error in print_complete_url(): no gnd number has been passed to connector object yet.") if self.show_printmessages else None
            return -1
    def return_complete_url(self, index = 0):
        if self.apiindex not in [i for i,_ in enumerate(self.apilist)]:
            print("connector.return_complete_url() error: apiindex is not defined correctly. using default api...") if self.show_printmessages else None
            self.apiindex = 0
        if self.gnd is not None:
            if type(self.gnd) == str:
                return self.apilist[self.apiindex]["baseUrl"].format(self.gnd)
            elif type(self.gnd) == list:
                return self.apilist[self.apiindex]["baseUrl"].format(self.gnd[index])
        else:
            print("connector error in return_complete_url(): no gnd number has been passed to connector object yet.") if self.show_printmessages else None
    def get_gnd_data(self, data_selection = None):
        if self.check_connectivity == False:
            print("connector note: connections to apis have not been checked yet. to do so manually execute connectivitycheck_loop() method of the current connector object. continuing attempt to receive gnd data from {} api...".format(self.apilist[self.apiindex]["name"])) if self.show_printmessages else None
        elif self.connection_established == False:
            print("connectivity error: after connectivity check no connection could has been established to any of the available apis. gnd data queries can not be executed at the moment.") if self.show_printmessages else None
            return None
        result = {}
        if type(self.gnd) == str:
            try:
                response = requests.get(self.return_complete_url())
                response.json()
            except:
                print("connectivity error in get_gnd_data() method: could not load resource from api as expected.") if self.show_printmessages else None
                return None
            self.connection_established = True
            if response.status_code == 200:
                result[self.gnd] = response.json()
                response.close()
                print("connector.get_gnd_data() status: data for gnd {} received.".format(self.gnd)) if self.show_printmessages else None
            else:
                print("connector.get_gnd_data() status: for gnd {} no data could be delivered by api".format(self.gnd)) if self.show_printmessages else None
                return None
        elif type(self.gnd) == list:
            for index, gnd in enumerate(self.gnd):
                try:
                    response = requests.get(self.return_complete_url(index))
                    response.json()
                except:
                    print("connectivity error in get_gnd_data() method: could not load resource from api as expected.") if self.show_printmessages else None
                    return None
                if response.status_code == 200:
                    result[gnd] = response.json()
                    response.close()
                    print("connector.get_gnd_data() status: gnd {} ({}) of {} processed".format(index + 1, gnd, len(self.gnd))) if self.show_printmessages else None
                else:
                    print("connector.get_gnd_data() status: for gnd {} ({}) of {} no data could be delivered by api".format(index + 1, gnd, len(self.gnd))) if self.show_printmessages else None
            self.connection_established = True
        #build new dict with selected values, which should be returned (base = all base aliases from apilist definition. list = select specific aliases from base set)
        def filter_received_data(gnd, mode):
            if mode == "base":
                base_categories = list(self.apilist[self.apiindex]["baseAliases"].keys())
                base_categories_data = {}
                for category in base_categories:
                    _temp_data = []
                    try:
                        _temp_data = result[gnd][self.apilist[self.apiindex]["baseAliases"][category][0]]
                    except KeyError:
                        _temp_data = []
                        print("connector.get_gnd_data() filtering note: could not find {} information for {} in raw data. continuing processing...".format(category, gnd)) if self.show_printmessages else None
                    #if information of a category is of categorial type itself, then rename the data delivered from the api according to the categorial definition in self.apilist
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
                    #add _temp_data value to return object
                    base_categories_data[category] = _temp_data
                return base_categories_data
            elif type(mode) == list:
                base_categories = list(self.apilist[self.apiindex]["baseAliases"].keys())
                selected_categories_data = {}
                for category in base_categories:
                    if category in mode:
                        _temp_data = []
                        try:
                            _temp_data = result[gnd][self.apilist[self.apiindex]["baseAliases"][category][0]]
                        except KeyError:
                            _temp_data = []
                            print("connector.get_gnd_data() filtering note: could not find {} information for {} in raw data. continuing processing...".format(category, gnd)) if self.show_printmessages else None
                        #if information of a category is of categorial type itself, then rename the data delivered from the api according to the categorial definition in self.apilist
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
                        #add _temp_data value to return object
                        selected_categories_data[category] = _temp_data
                return selected_categories_data
        if data_selection is not None:
            if type(self.gnd) == str:
                _new_dict = {list(result.keys())[0]: filter_received_data(self.gnd, data_selection)}
            elif type(self.gnd) == list:
                _new_dict = {}
                for key in result:
                    _new_dict[key] = filter_received_data(key, data_selection)
            result = _new_dict
        return result