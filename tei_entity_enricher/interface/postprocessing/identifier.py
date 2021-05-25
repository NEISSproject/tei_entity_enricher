from typing import Union, List, Tuple, Dict
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector

class Identifier:
    def __init__(self, \
                 input: Union[List[Tuple[str, str]], None] = None, \
                 current_result_data: Union[dict, None] = None, \
                 show_printmessages: bool = True) \
                 -> None:
        """delivers suggestions to which entity(ies) refers the input string(s)
        
        input: contains a list of tuples, which themself consists of a name and a type string
        show_printmessages: show class internal printmessages on runtime or not"""
        self.input: Union[List[Tuple[str, str]], None] = input
        self.current_result_data: Union[dict, None] = current_result_data
        self.show_printmessages: bool = show_printmessages

    def query(self, \
              filter_for_precise_spelling: bool = True, \
              filter_for_correct_type: bool = True) \
              -> Union[Dict[str, list], bool]:
        """starts wikidata query and saves results in self.current_result_data
        
        filter_for_precise_spelling variable determines wheather only exact matches
        between the search string and the label value in the search list returned by
        api are returned,
        filter_for_correct_type variable determines wheather the entities returned by api
        will be checked semantically with sparql queries in correspondance with the delivered
        type strings in self.input; only entities of a correct type will be returned"""
        c = WikidataConnector(self.input)
        result = c.get_wikidata_search_results(filter_for_precise_spelling, filter_for_correct_type)
        self.current_result_data = result
        return result

    def summarize_current_results(self) -> int:
        """prints found entities (entity name and description) to all tuples in self.input list,
        to deliver a human readable overview over self.current_result_data"""
        for key in self.current_result_data:
            print("{}: {}".format(key, self.current_result_data[key][0]))
            for hit in self.current_result_data[key][1]['search']:
                wikidataId = hit.get('id', 'No wikidata id delivered')
                descr = hit.get('description', 'No description delivered')
                print(f"----- {descr} -- {wikidataId}")

def identifier_demo(input):
    i = Identifier(input)

    print(f'\n\nIdentifier started, input: {input}\n\n\n---------------getting raw result------------------')
    i_result_raw = i.query(False, False)
    print('\n\nraw result\n##########')
    i.summarize_current_results()
    print('\n')
    print(i_result_raw)

    print('\n\n\n\n\n---------------getting spell filtered result------------------')
    i_result_spelling_filtered = i.query(True, False)
    print('\n\nfiltered result #1 (filtered by exact spelling)\n##########')
    i.summarize_current_results()
    print('\n')
    print(i_result_spelling_filtered)

    print('\n\n\n\n\n---------------getting type filtered result------------------')
    i_result_type_filtered = i.query(False, True)
    print('\n\nfiltered result #2 (filtered by type)\n##########')
    i.summarize_current_results()
    print('\n')
    print(i_result_type_filtered)

    print('\n\n\n\n\n\n---------------getting fully filtered result------------------')
    i_result_all_filtered = i.query()
    print('\n\nfiltered result #3 (filtered by spelling and by type)\n##########')
    i.summarize_current_results()
    print('\n')
    print(i_result_all_filtered)

if __name__ == '__main__':
    identifier_demo([('Mecklenburg', 'place'), ('Schwerin', 'place'), ('Roger Labahn', 'person'), ('Uwe Johnson Gesellschaft', 'organisation'), ('Rostock', 'place'), ('Bertolt Brecht', 'person')])