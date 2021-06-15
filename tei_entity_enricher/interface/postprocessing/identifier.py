from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from typing import Union, List, Tuple, Dict
from tei_entity_enricher.interface.postprocessing.wikidata_connector import (
    WikidataConnector,
)
from tei_entity_enricher import __version__
from SPARQLWrapper import SPARQLWrapper, JSON


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

    def check_entity_library_by_names_and_type(
        self, input_tuple: tuple = None, loaded_library: EntityLibrary = None
    ) -> Dict[Tuple[str, str], List[dict]]:
        """checks name, furtherNames and type values of loaded_library
        for input_tuple and returns a list of entity dicts as value;
        a found entity must be of the correct type and has to have the name
        either in the name key or in the furtherNames key"""
        searchstring_name = input_tuple[0]
        searchstring_type = input_tuple[1]
        result_list = list(
            filter(
                lambda item: (item["type"] == searchstring_type)
                and ((item["name"] == searchstring_name) or (searchstring_name in item["furtherNames"]))
            )
        )
        return result_list

    def check_query_results_with_wikidata_ids_of_entity_library(
        self, loaded_library: EntityLibrary = None, library_files: List[str] = None
    ) -> Union[Dict[str, dict], dict]:
        """checks results of self.query() by wikidata_id value refering to entity library
        and returns a dict with name values as keys and entity dicts as values"""
        pass

    def get_gnd_id_of_wikidata_entity(self, wikidata_id: str):
        query = """
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>

            SELECT ?o
            WHERE
            {
                wd:%s wdt:P227 ?o .
            }
            """
        endpoint_url = "https://query.wikidata.org/sparql"
        user_agent = "NEISS TEI Entity Enricher v.{}".format(__version__)
        sparql = SPARQLWrapper(endpoint=endpoint_url, agent=user_agent)
        sparql.setQuery(query % wikidata_id)
        sparql.setReturnFormat(JSON)
        result = sparql.query().convert()
        return result["results"]["bindings"]
        # if there is no result, the bindings is an empty list
        # if there is a result, it can be retrieved by returnvalue[0]["o"]["value"]

    # todo: funktionen schreiben: neuaufnahme von entitäten in die library, finale empfehlungen ausgeben

    def suggest(
        self,
        query_entity_library: Union[EntityLibrary, None] = None,
        wikidata_filter_for_precise_spelling: bool = True,
        wikidata_filter_for_correct_type: bool = True,
        wikidata_web_api_language: str = "de",
        wikidata_web_api_limit: str = "50",
        check_connectivity_to_wikidata: bool = False,
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

        {
            ('Berlin', 'place'): [
                {"name": "Berlin", "furtherNames": [], "type": "place", "wikidata_id": "Q64", "gnd_id": ""},
                {}
            ]
        }

        """
        if query_entity_library is not None:
            query_entity_library_result = {}
            for tuple in self.input:
                tuple_result_list = self.check_entity_library_by_names_and_type(tuple, query_entity_library)
                query_entity_library_result[tuple] = tuple_result_list
        query_wikidata_result = {}
        query_wikidata_result = self.wikidata_query(
            wikidata_filter_for_precise_spelling,
            wikidata_filter_for_correct_type,
            wikidata_web_api_language,
            wikidata_web_api_limit,
            check_connectivity_to_wikidata,
        )
        output_dict = {}
        if query_entity_library is not None:
            # wenn beides, entity library und wikidata check, durchgeführt wurden
            if len(query_entity_library_result) > 0:
                if len(query_wikidata_result) > 0:
                    # wenn beide, entity library check und wikidata check, jeweils mindestens eine entität geliefert haben
                    pass
                else:
                    # wenn nur entity library check mindestens eine entität geliefert hat
                    pass
            else:
                if len(query_wikidata_result) > 0:
                    # wenn nur wikidata check mindestens eine entität geliefert hat
                    pass
                else:
                    # wenn keine, weder entity library noch wikidata, entitäten geliefert haben
                    pass
        else:
            # wenn nur der wikidata check durchgeführt wurde
            if len(query_wikidata_result) > 0:
                # wenn der wikidata check mindestens eine entität geliefert hat
                pass
            else:
                # wenn der wikidata check keine entitäten geliefert hat
                pass

        """
        HIER WEITER
        """
        # beide möglichen ergebnisse zu einem dict zusammensetzen (nach überschneidungen via wikidata_id schauen, einheitliches format erzeugen)

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
