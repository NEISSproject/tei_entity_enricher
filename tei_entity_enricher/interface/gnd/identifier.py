from typing import List, Tuple, Dict
from tei_entity_enricher.interface.gnd.io import FileReader

class Identifier:
    def __init__(self, \
                 input: List[Tuple[str, str]] = None, \
                 show_printmessages: bool = True) \
                 -> None:
        """returns suggestions to which entity(ies) refers input string(s)
        
        input: contains a list of tuples, which themself consists of a name and a type string
        show_printmessages: show class internal printmessages on runtime or not"""
        self.input: List[Tuple[str, str]] = input
        self.show_printmessages: bool = show_printmessages

    def get_wikidata_search_results(self, \
                                    filter_for_precise_hits: bool = True) \
                                    -> Dict[str, list]:
        """sends a entity query to wikidata api using input strings of self.input
        and returns a dict with input strings as keys and a list as values,
        which consists of the number of search hits and the returned data object,
        filter_for_precise_hits variable determines wheather only exact matches
        between the search string and the label value in the search list returned by
        api are returned"""
        result_dict = {}
        for string_tuple in self.input:
            filereader = FileReader("https://www.wikidata.org/w/api.php?action=wbsearchentities&search={}&format=json&language=de".format(string_tuple[0]), "web", True, True)
            filereader_result = filereader.loadfile_json()
            if filter_for_precise_hits == True:
                precise_hits = []
                for search_list_element in filereader_result['search']:
                    if search_list_element['label'] == string_tuple[0]:
                        precise_hits.append(search_list_element)
                filereader_result['search'] = precise_hits
            result_dict[string_tuple[0]] = [len(filereader_result['search']), filereader_result]
        return result_dict