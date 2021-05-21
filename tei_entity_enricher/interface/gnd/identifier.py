from typing import Union, List, Tuple, Dict
from SPARQLWrapper import SPARQLWrapper, JSON
from tei_entity_enricher.interface.gnd.io import FileReader
import math

class Identifier:
    def __init__(self, \
                 input: Union[List[Tuple[str, str]], None] = None, \
                 show_printmessages: bool = True) \
                 -> None:
        """returns suggestions to which entity(ies) refers the input string(s)
        
        input: contains a list of tuples, which themself consists of a name and a type string
        show_printmessages: show class internal printmessages on runtime or not"""
        self.input: Union[List[Tuple[str, str]], None] = input
        self.show_printmessages: bool = show_printmessages

    def get_wikidata_search_results(self, \
                                    filter_for_precise_spelling: bool = True, \
                                    filter_for_correct_type: bool = True) \
                                    -> Union[Dict[str, list], bool]:
        """sends a entity query to wikidata api using input strings of self.input
        and returns a dict with input strings as keys and a list as values,
        which consists of the number of search hits and the returned data object,
        filter_for_precise_spelling variable determines wheather only exact matches
        between the search string and the label value in the search list returned by
        api are returned,
        filter_for_correct_type variable determines wheather the entities returned by api
        will be checked semantically with sparql queries in correspondance with the delivered
        type strings in self.input; only entities of a correct type will be returned"""
        if self.input == None:
            print('Identifier.get_wikidata_search_results() Error: Identifier has no input data.') if self.show_printmessages == True else None
            return False
        if (type(self.input) != list) or (len(self.input) < 1) or (type(self.input[0]) != tuple) or (type(self.input[0][0]) != str):
            print('Identifier.get_wikidata_search_results() Error: Identifier input data is in a wrong format.') if self.show_printmessages == True else None
            return False
        result_dict = {}
        for string_tuple in self.input:
            filereader = FileReader("https://www.wikidata.org/w/api.php?action=wbsearchentities&search={}&format=json&language=de".format(string_tuple[0]), "web", True, self.show_printmessages)
            filereader_result = filereader.loadfile_json()
            if not filter_for_precise_spelling == True and not filter_for_correct_type == True:
                print(f"no filtering in {string_tuple} result") if self.show_printmessages == True else None
            if filter_for_precise_spelling == True:
                precise_spelling = []
                entry_amount = len(filereader_result['search'])
                percent = 100 / entry_amount if entry_amount > 0 else 100
                progressbar = 0
                for search_list_element in filereader_result['search']:
                    progressbar += percent
                    print(f"spell filtering in {string_tuple} result: {math.floor(progressbar * 10 ** 2) / 10 ** 2}") if self.show_printmessages == True else None
                    if search_list_element['label'] == string_tuple[0]:
                        precise_spelling.append(search_list_element)
                filereader_result['search'] = precise_spelling
            if filter_for_correct_type == True:
                correct_type = []
                entry_amount = len(filereader_result['search'])
                percent = 100 / entry_amount if entry_amount > 0 else 100
                progressbar = 0
                for search_list_element in filereader_result['search']:
                    progressbar += percent
                    print(f"type filtering in {string_tuple} result: {math.floor(progressbar * 10 ** 2) / 10 ** 2}") if self.show_printmessages == True else None
                    if self.check_wikidata_entity_type(search_list_element['id'], string_tuple[1]) == True:
                        correct_type.append(search_list_element)
                filereader_result['search'] = correct_type
            result_dict[string_tuple[0]] = [len(filereader_result['search']), filereader_result]
        return result_dict

    def check_wikidata_entity_type(self, \
                                   entity_id: str, \
                                   type: str) \
                                   -> bool:
        """used in get_wikidata_search_results() to check, if those wikidata entities delivered
        by self.get_wikidata_search_results() query are of the type, which has been defined inside
        the self.input tuples of Identifier class
        
        this check uses the wikidata semantic web data base by sending queries to the wikidata sparql endpoint;
        get_wikidata_search_results() retrieves wikidata id numbers, which are used here in an ASK-query,
        which determines, if the entity in question is a member of one of specific classes
        (see 'queries' variable for details: 'wdt:P31/wdt:P279*'-property means 'is a member of a specific class or
        a member of any subclass (any level above) of a specific class' and the FILTER statement defines a set of classes,
        out of which only one class has to match the query statement to let the query return true)

        a sparqle query to wikidata endpoint needs an agent parameter in the header to get an answer,
        the value of the agent string can be choosen freely

        this method checks only one entity at once and has to be used in an iteration
        
        """
        # todo: import __version__ variable from __init__.py
        __version__ = '0.0.0'
        endpoint_url = "https://query.wikidata.org/sparql"
        user_agent = 'NEISS TEI Enricher v.{}'.format(__version__)
        
        queries = {
            'person': [
                """
                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                    PREFIX wd: <http://www.wikidata.org/entity/>

                    ASK
                    {
                    wd:%s wdt:P31/wdt:P279* ?o .
                    FILTER (?o IN (wd:Q5))
                    }
                """,
                """
                    q5 = human
                """
            ],
            'organisation': [
                """
                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                    PREFIX wd: <http://www.wikidata.org/entity/>

                    ASK
                    {
                    wd:%s wdt:P31/wdt:P279* ?o .
                    FILTER (?o IN (wd:Q43229))
                    }
                """,
                """
                    Q43229 = organization
                """
            ],
            'place': [
                """
                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                    PREFIX wd: <http://www.wikidata.org/entity/>

                    ASK
                    {
                    wd:%s wdt:P31/wdt:P279* ?o .
                    FILTER (?o IN (wd:Q515, wd:Q27096213))
                    }
                """,
                """
                    Q515 = city
                    Q27096213 = geographic entity

                    note: at the moment this category includes the categories 'city', 'ground' and 'water',
                    which should be differentiated
                """
            ],
        }

        sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
        sparql.setQuery(queries.get(type)[0]%entity_id)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()['boolean']

def identifier_demo(input):
    i = Identifier(input)

    print(f'\n\nIdentifier started, input: {input}\n\n\n---------------getting raw result------------------')
    i_result_raw = i.get_wikidata_search_results(False, False)
    print('\n\nraw result\n##########')
    for key in i_result_raw:
        print("{}: {}".format(key, i_result_raw[key][0]))
        for hit in i_result_raw[key][1]['search']:
            descr = hit.get('description', 'No description delivered')
            print(f"----- {descr}")
    print('\n')
    print(i_result_raw)

    print('\n\n\n\n\n---------------getting spell filtered result------------------')
    i_result_spelling_filtered = i.get_wikidata_search_results(True, False)
    print('\n\nfiltered result #1 (filtered by exact spelling)\n##########')
    for key in i_result_spelling_filtered:
        print("{}: {}".format(key, i_result_spelling_filtered[key][0]))
        for hit in i_result_spelling_filtered[key][1]['search']:
            descr = hit.get('description', 'No description delivered')
            print(f"----- {descr}")
    print('\n')
    print(i_result_spelling_filtered)

    print('\n\n\n\n\n---------------getting type filtered result------------------')
    i_result_type_filtered = i.get_wikidata_search_results(False, True)
    print('\n\nfiltered result #2 (filtered by type)\n##########')
    for key in i_result_type_filtered:
        print("{}: {}".format(key, i_result_type_filtered[key][0]))
        for hit in i_result_type_filtered[key][1]['search']:
            descr = hit.get('description', 'No description delivered')
            print(f"----- {descr}")
    print('\n')
    print(i_result_type_filtered)

    print('\n\n\n\n\n\n---------------getting fully filtered result------------------')
    i_result_all_filtered = i.get_wikidata_search_results()
    print('\n\nfiltered result #3 (filtered by spelling and by type)\n##########')
    for key in i_result_all_filtered:
        print("{}: {}".format(key, i_result_all_filtered[key][0]))
        for hit in i_result_all_filtered[key][1]['search']:
            descr = hit.get('description', 'No description delivered')
            print(f"----- {descr}")
    print('\n')
    print(i_result_all_filtered)

if __name__ == '__main__':
    identifier_demo([('Mecklenburg', 'place'), ('Roger Labahn', 'person'), ('Uwe Johnson Gesellschaft', 'organisation'), ('Rostock', 'place')])