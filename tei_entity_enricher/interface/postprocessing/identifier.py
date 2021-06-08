from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from typing import Union, List, Tuple, Dict
from tei_entity_enricher.interface.postprocessing.wikidata_connector import (
    WikidataConnector,
)


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
        current_result_data:
            buffer to save and print current query results"""
        self.input: Union[List[Tuple[str, str]], None] = input
        self.show_printmessages: bool = show_printmessages
        self.current_result_data: Union[dict, None] = None

    def check_entity_library_by_name(
        self, input_tuple: tuple = None, loaded_library: EntityLibrary = None
    ) -> Dict[Tuple[str, str], List[dict]]:
        """checks name and furtherNames values of loaded_library
        for input_tuple and returns a dict with input_tuple as key and a list of entity dicts as value"""
        pass
        # search entitys of correct typ
        # in this results search name and furtherNames values

    def check_query_results_with_wikidata_ids_of_entity_library(
        self, loaded_library: EntityLibrary = None, library_files: List[str] = None
    ) -> Union[Dict[str, dict], dict]:
        """checks results of self.query() by wikidata_id value refering to entity library
        and returns a dict with name values as keys and entity dicts as values"""
        pass

    # todo: funktionen schreiben: neuaufnahme von entitäten in die library, finale empfehlungen ausgeben

    def suggest(
        self,
        query_entity_library: Union[EntityLibrary, None] = None,
        wikidata_filter_for_precise_spelling: bool = True,
        wikidata_filter_for_correct_type: bool = True,
        wikidata_web_api_language: str = "de",
        wikidata_web_api_limit: str = "50",
    ) -> Dict[Tuple[str, str], List[dict]]:
        """delivers entity suggestions to tuples in self.input,
        returns dict with tuples as keys and entity list as values,
        uses entity library query and wikidata queries,
        if no reference to a active library instance is given in query_entity_library,
        no entity library query is executed

        {
            ('Berlin', 'place'): [
                {"name": "Berlin", "furtherNames": [], "type": "place", "wikidata_id": "Q64", "gnd_id": ""},
                {}
            ]
        }

        {
            'Berlin': [
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

        """
        if query_entity_library is not None:
            query_entity_library_result = {}
            for tuple in self.input:
                tuple_result = self.check_entity_library_by_name(tuple, query_entity_library)
                query_entity_library_result.update(tuple_result)
            query_wikidata_result = {}
            # HIER WEITER: wikidata-abfragen machen
            # beide ergebnisse zu einem dict zusammensetzen (nach überschneidungen via wikidata_id schauen, einheitliches format erzeugen)

    def wikidata_query(
        self,
        filter_for_precise_spelling: bool = True,
        filter_for_correct_type: bool = True,
        wikidata_web_api_language: str = "de",
        wikidata_web_api_limit: str = "50",
        check_connectivity: bool = False,
    ) -> Union[Dict[str, list], bool]:
        """starts wikidata query and saves results in self.current_result_data

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
        self.current_result_data = result
        return result

    def summarize_current_results(self) -> int:
        """prints found entities (entity name and description) to all tuples in self.input list,
        to deliver a human readable overview over self.current_result_data"""
        for key in self.current_result_data:
            print(f"{key}: {self.current_result_data[key][0]}")
            for hit in self.current_result_data[key][1]["search"]:
                wikidataId = hit.get("id", "No wikidata id delivered")
                descr = hit.get("description", "No description delivered")
                print(f"----- {descr} -- {wikidataId}")
