from typing import Union, List, Tuple, Dict
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from tei_entity_enricher.interface.postprocessing.wikidata_connector import (
    WikidataConnector,
)
from tei_entity_enricher.interface.postprocessing.io import Cache
from tei_entity_enricher import __version__


class Identifier:
    def __init__(
        self,
        input: Union[List[Tuple[str, str]], None] = None,
        show_printmessages: bool = True,
    ) -> None:
        """delivers suggestions to which entity(ies) refers the input string(s)

        input:
            contains a list of tuples, which themself consists of a name and a type string
        show_printmessages:
            show class internal printmessages on runtime or not
        current_wikidata_query_result_data:
            buffer to save and print current wikidata_query() results
        current_suggest_result_data:
            buffer to save and print current suggest() results
        entity_types:
            list of entity types currently used in ntee, retrieved from sparql_queries.json"""
        self.input: Union[List[Tuple[str, str]], None] = input
        self.show_printmessages: bool = show_printmessages
        self.current_wikidata_query_result_data: Union[dict, None] = None
        self.current_suggest_result_data: Union[dict, None] = None
        self.entity_types: List[str] = self.get_entity_type_list()

    def get_entity_type_list(self) -> List[str]:
        wikidata_con = WikidataConnector(check_connectivity=False, show_printmessages=False)
        return list(wikidata_con.wikidata_sparql_queries.keys())

    def check_entity_library_by_names_and_type(
        self, input_tuple: tuple = None, loaded_library: EntityLibrary = None
    ) -> List[dict]:
        """checks name, furtherNames and type values of loaded_library
        for input_tuple and returns a list of entity dicts as value;
        a found entity must be of the correct type and has to have the name
        either in the name key or in the furtherNames key"""
        searchstring_name = input_tuple[0]
        searchstring_type = input_tuple[1]
        result_list = list(
            filter(
                lambda item: (item["type"] == searchstring_type)
                and ((item["name"] == searchstring_name) or (searchstring_name in item["furtherNames"])),
                loaded_library.data,
            )
        )
        return result_list

    def check_query_results_with_wikidata_ids_of_entity_library(
        self, loaded_library: EntityLibrary = None, library_files: List[str] = None
    ) -> Union[Dict[str, dict], dict]:
        """checks results of self.query() by wikidata_id value refering to entity library
        and returns a dict with name values as keys and entity dicts as values"""
        pass

    def check_wikidata_result_has_data(self, wikidata_result: Dict[Tuple[str, str], list]) -> bool:
        """checks length of dict and integer in dict[key] list on index 0,
        which shows the length of the list in dict[key][1] (the amount of entity dicts in dict[key][1])"""
        result = False
        if len(wikidata_result) > 0:
            for key in wikidata_result:
                if wikidata_result[key][0] > 0:
                    result = True
        return result

    def check_entity_library_result_has_data(self, entity_library_result: Dict[Tuple[str, str], List[dict]]) -> bool:
        result = False
        if len(entity_library_result) > 0:
            for key in entity_library_result:
                if len(entity_library_result[key]) > 0:
                    result = True
        return result

    # todo: funktionen schreiben: neuaufnahme von entitäten in die library, finale empfehlungen ausgeben

    def suggest(
        self,
        query_entity_library: Union[EntityLibrary, None] = None,
        do_wikidata_query: bool = True,
        wikidata_filter_for_precise_spelling: bool = True,
        wikidata_filter_for_correct_type: bool = True,
        wikidata_web_api_language: str = "de",
        wikidata_web_api_limit: str = "50",
        check_connectivity_to_wikidata: bool = False,
    ) -> Union[Dict[Tuple[str, str], List[dict]], dict]:
        """delivers entity suggestions to tuples in self.input,
        returns dict with tuples as keys and entity list (list of dicts, whoses structure corresponds
        to entity library entity structure) as values or returns an empty dict, if no suggestions could be made,
        uses entity library query and wikidata queries,
        if no reference to a active library instance is given in query_entity_library,
        no entity library query is executed

        entity library query result:
        {
            ('Berlin', 'place'): [
                {"name": "Berlin", "furtherNames": [], "type": "place", "description": "", "wikidata_id": "Q64", "gnd_id": ""},
                {}
            ]
        }

        wikidata query result:
        {
            ('Berlin', 'place'): [
                4,
                {
                    "searchinfo": {},
                    "search": [
                    {"id": "Q64",..., "label": "Berlin", "description": "federal state, capital and largest city of Germany"},
                    {'id': 'Q821244', ...., 'label': 'Berlin', 'description': 'city in Coos County, New Hampshire, USA'}
                    ],
                    ...,
                    "success": 1
                }
            ]
        }

        output:
        {
            ('Berlin', 'place'): [
                {"name": "Berlin", "furtherNames": [], "type": "place", "description": "", "wikidata_id": "Q64", "gnd_id": ""},
                {}
            ]
        }

        """
        # retrieve data
        query_entity_library_result = {}
        entity_library_has_data = None
        if query_entity_library is not None:
            for tuple in self.input:
                tuple_result_list = self.check_entity_library_by_names_and_type(tuple, query_entity_library)
                query_entity_library_result[tuple] = tuple_result_list
            entity_library_has_data = self.check_entity_library_result_has_data(query_entity_library_result)
        query_wikidata_result = {}
        if do_wikidata_query == True:
            query_wikidata_result = self.wikidata_query(
                wikidata_filter_for_precise_spelling,
                wikidata_filter_for_correct_type,
                wikidata_web_api_language,
                wikidata_web_api_limit,
                check_connectivity_to_wikidata,
            )
        wikidata_result_has_data = (
            self.check_wikidata_result_has_data(query_wikidata_result) if do_wikidata_query == True else False
        )
        # create output
        output_dict = {}
        if query_entity_library is not None:
            # if both, entity library check and wikidata check, were executed
            if entity_library_has_data:
                if wikidata_result_has_data:
                    # if both, entity library check and wikidata check, suggested any entities
                    wikidata_output_dict = {}
                    _temp_el = EntityLibrary(show_printmessages=False)
                    for key in query_wikidata_result:
                        entity_list_in_query_wikidata_result = []
                        for subkey in query_wikidata_result[key][1]["search"]:
                            _gnd_retrieve_attempt_result = _temp_el.get_gnd_id_of_wikidata_entity(subkey["id"])
                            _gnd_id_to_add = (
                                _gnd_retrieve_attempt_result[0]["o"]["value"]
                                if len(_gnd_retrieve_attempt_result) > 0
                                else ""
                            )
                            entity_list_in_query_wikidata_result.append(
                                {
                                    "name": subkey.get("label", f"No name delivered, search pattern was: {key[0]}"),
                                    "furtherNames": [],
                                    "type": key[1],
                                    "description": subkey.get("description", "No description delivered"),
                                    "wikidata_id": subkey.get("id", ""),
                                    "gnd_id": _gnd_id_to_add,
                                }
                            )
                        wikidata_output_dict[key] = entity_list_in_query_wikidata_result
                    redundancy_test_list = []
                    for tuple in query_entity_library_result:
                        check_cache = Cache(query_entity_library_result[tuple])
                        for entity in wikidata_output_dict[tuple]:
                            _temp_check_result_tuple = check_cache.check_for_redundancy(
                                usecase="EntityLibrary", wikidata_id=entity["wikidata_id"], gnd_id=entity["gnd_id"]
                            )
                            if _temp_check_result_tuple[0] == True:
                                redundancy_test_list.append(entity["wikidata_id"])
                            if _temp_check_result_tuple[1] == True:
                                redundancy_test_list.append(entity["gnd_id"])
                        for item in redundancy_test_list:
                            wikidata_output_dict[tuple] = list(
                                filter(
                                    lambda x: (x.get("wikidata_id") != item) and (x.get("gnd_id") != item),
                                    wikidata_output_dict[tuple],
                                )
                            )
                        query_entity_library_result[tuple].extend(wikidata_output_dict[tuple])
                        output_dict[tuple] = query_entity_library_result[tuple]
                else:
                    # if only entity library check suggested any entities
                    output_dict = query_entity_library_result
            else:
                if wikidata_result_has_data:
                    # if only wikidata check suggested any entities
                    _temp_el = EntityLibrary(show_printmessages=False)
                    for key in query_wikidata_result:
                        entity_list_in_query_wikidata_result = []
                        for subkey in query_wikidata_result[key][1]["search"]:
                            _gnd_retrieve_attempt_result = _temp_el.get_gnd_id_of_wikidata_entity(subkey["id"])
                            _gnd_id_to_add = (
                                _gnd_retrieve_attempt_result[0]["o"]["value"]
                                if len(_gnd_retrieve_attempt_result) > 0
                                else ""
                            )
                            entity_list_in_query_wikidata_result.append(
                                {
                                    "name": subkey.get("label", f"No name delivered, search pattern was: {key[0]}"),
                                    "furtherNames": [],
                                    "type": key[1],
                                    "description": subkey.get("description", "No description delivered"),
                                    "wikidata_id": subkey.get("id", ""),
                                    "gnd_id": _gnd_id_to_add,
                                }
                            )
                        output_dict[key] = entity_list_in_query_wikidata_result
                else:
                    # if none of the two checks, entity library and wikidata, suggested any entities
                    output_dict = {}
        else:
            # if only wikidata check was executed
            if wikidata_result_has_data:
                # if wikidata check suggested any entities
                _temp_el = EntityLibrary(show_printmessages=False)
                for key in query_wikidata_result:
                    entity_list_in_query_wikidata_result = []
                    for subkey in query_wikidata_result[key][1]["search"]:
                        _gnd_retrieve_attempt_result = _temp_el.get_gnd_id_of_wikidata_entity(subkey["id"])
                        _gnd_id_to_add = (
                            _gnd_retrieve_attempt_result[0]["o"]["value"]
                            if len(_gnd_retrieve_attempt_result) > 0
                            else ""
                        )
                        entity_list_in_query_wikidata_result.append(
                            {
                                "name": subkey.get("label", f"No name delivered, search pattern was: {key[0]}"),
                                "furtherNames": [],
                                "type": key[1],
                                "description": subkey.get("description", "No description delivered"),
                                "wikidata_id": subkey.get("id", ""),
                                "gnd_id": _gnd_id_to_add,
                            }
                        )
                    output_dict[key] = entity_list_in_query_wikidata_result
            else:
                # if wikidata check suggested no entities
                output_dict = {}
        self.current_suggest_result_data = output_dict
        return output_dict

    def wikidata_query(
        self,
        filter_for_precise_spelling: bool = True,
        filter_for_correct_type: bool = True,
        wikidata_web_api_language: str = "de",
        wikidata_web_api_limit: str = "50",
        check_connectivity: bool = False,
    ) -> Union[Dict[Tuple[str, str], list], bool]:
        """starts wikidata query and saves results in self.current_wikidata_query_result_data

        filter_for_precise_spelling:
            variable determines wheather only exact matches
            between the search string and the label value in the search list returned by
            api are returned (filtering is executed only if there are more than 5 search hits,
            otherwise it is not executed although filter_for_precise_spelling is True),
        filter_for_correct_type:
            variable determines wheather the entities returned by api
            will be checked semantically with sparql queries in correspondance with the delivered
            type strings in self.input; only entities of a correct type will be returned
        check_connectivity:
            execute connectivity check in called WikidataConnector instance or not
        """
        c = WikidataConnector(
            self.input,
            check_connectivity,
            wikidata_web_api_language,
            wikidata_web_api_limit,
            self.show_printmessages,
        )
        result = c.get_wikidata_search_results(filter_for_precise_spelling, filter_for_correct_type)
        self.current_wikidata_query_result_data = result
        return result

    def summarize_current_wikidata_query_results(self) -> None:
        """prints found entities (entity name and description) to all tuples in self.input list,
        to deliver a human readable overview over self.current_wikidata_query_result_data"""
        for key in self.current_wikidata_query_result_data:
            print(f"{key}: {self.current_wikidata_query_result_data[key][0]}")
            for hit in self.current_wikidata_query_result_data[key][1]["search"]:
                wikidataId = hit.get("id", "No wikidata id delivered")
                descr = hit.get("description", "No description delivered")
                print(f"----- {descr} -- {wikidataId}")

    def summarize_current_suggest_results(self) -> None:
        """prints found entities (entity name and description) to all tuples in self.input list,
        to deliver a human readable overview over self.current_suggest_result_data"""
        for key in self.current_suggest_result_data:
            print(f"{key}: {len(self.current_suggest_result_data[key])}")
            for entity in self.current_suggest_result_data[key]:
                wikidataId = entity.get("wikidata_id", "No wikidata id delivered")
                descr = entity.get("description", "No description delivered")
                print(f"----- {descr} -- {wikidataId}")


if __name__ == "__main__":

    def test(with_wikidata_query: bool = True):
        input = [("Berlin", "place"), ("Steven Spielberg", "person"), ("UNO", "organisation"), ("Steve", "person")]
        i = Identifier(input)
        el = EntityLibrary(use_default_data_file=True)
        suggestions = i.suggest(el, with_wikidata_query)
        print(suggestions)
        i.summarize_current_suggest_results()

    test(with_wikidata_query=True)
