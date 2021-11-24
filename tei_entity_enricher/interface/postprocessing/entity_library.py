from typing import Union, List, Tuple
from streamlit.uploaded_file_manager import UploadedFile
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter, Cache
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector
from tei_entity_enricher.interface.postprocessing.gnd_connector import GndConnector
from tei_entity_enricher.util.helper import local_save_path, makedir_if_necessary
from tei_entity_enricher.util.exceptions import MissingDefinition, FileNotFound, BadFormat
import os
from urllib.parse import urlparse
from tei_entity_enricher import __version__
from SPARQLWrapper import SPARQLWrapper, JSON

# todo: prüfen, wie furtherIds im Moment zu Entitäten in der entity library hinzugefügt werden können
# todo: wahrscheinlich furtherIds-Befüllung in add_missing_ids() einbauen


class EntityLibrary:
    def __init__(
        self,
        data_file: Union[str, None] = None,
        use_default_data_file: bool = False,
        show_printmessages: bool = True,
    ) -> None:
        """is a runtime memory of entities (saved properties are: name, furtherNames, type, gnd_id, wikidata_id),
        which is used as data source for named entity identification in post-processing

        it can be build up manually or inside an identification pipeline, where wikidata entity search results
        can be enriched by data retrieved by GndConnector and alltogether added to EntityLibrary

        data_file:
            path to json file, from which data is loaded and to which the data should be saved to
        use_default_data_file:
            load EntityLibrary with default data_file-path or not
        show_printmessages:
            show class internal printmessages on runtime or not
        default_data_file:
            default path to json file in local_save_path/config/postprocessing/entity_library.json, is saved here and not
            as default value on init for processing reasons in menu/tei_postprocessing.py
        data:
            currently loaded dict, is loaded from json file on __init__(), if a correct filepath in data_file is provided
        furtherIds_config:
            dict loaded from file, which contains database information for NEL in postprocessing
            (keys are hostnames and values are lists,
            containing 1.: the wikidata property id which is used to retrieve the respective Identifier information from wikidata sparql endpoint,
            2. a uri template with a blank, in which an id can be inserted later to create a specific entitiy uri for the respective database)
        """
        self.use_default_data_file: bool = use_default_data_file
        self.default_data_file: str = os.path.join(local_save_path, "config", "postprocessing", "entity_library.json")
        self.data_file: Union[str, None] = self.default_data_file if self.use_default_data_file == True else data_file
        self.show_printmessages: bool = show_printmessages
        self.data: Union[list, None] = None
        if (self.data_file is not None) and (self.load_library(create_new_file=True) == True):
            print(f"EntityLibrary loaded from {self.data_file}...") if self.show_printmessages else None
        else:
            print("EntityLibrary initialized without data...") if self.show_printmessages else None
        self.furtherIds_config: Union[dict, None] = self.load_furtherIds_config()

    def load_furtherIds_config(self) -> None:
        """used to load furtherIds_config.json from a local json file in config folder;
        file defines which ids (besides compulsory gnd and wikidata) are saved in entity dicts
        and which databases can be selected in manual postprocessing menu for adding reference uris as attribute to xml elements"""
        default_filepath = os.path.join(local_save_path, "config", "postprocessing", "furtherIds_config.json")
        fr = FileReader(
            filepath=default_filepath, origin="local", internal_call=True, show_printmessages=self.show_printmessages
        )
        result = None
        try:
            result = fr.loadfile_json()
        except FileNotFound:
            print(
                f"EntityLibrary load_furtherIds_config(): could not load furtherIds_config.json from config folder, file not found. creating default config file..."
            ) if self.show_printmessages else None
            try:
                makedir_if_necessary(os.path.dirname(default_filepath))
                FileWriter(
                    data={
                        "geonames.com": ["wdt:P1566", "https://www.geonames.org/{}"],
                        "viaf.org": ["wdt:P214", "https://viaf.org/viaf/{}"],
                    },
                    filepath=default_filepath,
                    show_printmessages=self.show_printmessages,
                ).writefile_json()
            except:
                print(
                    f"EntityLibrary load_furtherIds_config(): could not create default furtherIds_config.json in config folder."
                ) if self.show_printmessages == True else None
                return f"EntityLibrary load_furtherIds_config(): could not create default furtherIds config in config folder."
            result = fr.loadfile_json()
        except BadFormat:
            print(
                f"EntityLibrary load_furtherIds_config(): could not load furtherIds_config.json from config folder, no valid json format."
            ) if self.show_printmessages else None
            return f"EntityLibrary load_furtherIds_config(): could not load furtherIds_config.json from config folder, no valid json format."
        return result

    def load_library(self, create_new_file: bool = False) -> Union[bool, str]:
        """used to load existing library data from a local json file with filepath saved in self.data_file"""
        if self.data_file is None:
            raise MissingDefinition("data_file", "EntityLibrary", "load_library()")
        fr = FileReader(
            filepath=self.data_file, origin="local", internal_call=True, show_printmessages=self.show_printmessages
        )
        result = None
        try:
            result = fr.loadfile_json()
        except FileNotFound:
            if create_new_file == True:
                print(
                    f"EntityLibrary load_library(): could not load library from {self.data_file}, file not found. creating default library file..."
                ) if self.show_printmessages else None
                try:
                    makedir_if_necessary(os.path.dirname(self.data_file))
                    FileWriter(
                        data=[
                            {
                                "name": "Berlin",
                                "furtherNames": [],
                                "type": "place",
                                "description": "",
                                "wikidata_id": "",
                                "gnd_id": "",
                                "furtherIds": {},
                            }
                        ],
                        filepath=self.data_file,
                        show_printmessages=self.show_printmessages,
                    ).writefile_json()
                except:
                    print(
                        f"EntityLibrary load_library(): could not create default entity_library.json in config folder."
                    ) if self.show_printmessages == True else None
                    return (
                        f"EntityLibrary load_library(): could not create default entity_library.json in config folder."
                    )
                result = fr.loadfile_json()
            else:
                print(
                    f"EntityLibrary load_library(): could not load library from {self.data_file}, file not found."
                ) if self.show_printmessages else None
                return f"EntityLibrary load_library(): could not load library from {self.data_file}, file not found."
        except BadFormat:
            print(
                f"EntityLibrary load_library(): could not load library from {self.data_file}, no valid json format."
            ) if self.show_printmessages else None
            return f"EntityLibrary load_library(): could not load library from {self.data_file}, no valid json format."
        structure_check_cache = Cache(result)
        if structure_check_cache.check_json_structure("EntityLibrary") == False:
            print(
                f"EntityLibrary load_library(): could not load library from {self.data_file}, file does not fulfill the structure requirements for EntityLibrary. See documentation for requirement list."
            ) if self.show_printmessages else None
            return f"EntityLibrary load_library(): could not load library from {self.data_file}, file does not fulfill the structure requirements for EntityLibrary. See documentation for requirement list."
        self.data = result
        return True

    def add_entities_from_file(
        self,
        source_path: str = None,
        origin: str = "local",
        source_type: str = None,
        file: UploadedFile = None,
        csv_delimiter: str = ",",
    ) -> Union[Tuple[int, int], str, None]:
        """used to add data from source (json or csv format) into the already loaded entity library

        source_path:
            uri or filepath in local system to source, from which entities should be added to library
        origin:
            source setting for used FileReader, can be 'web' or 'local'
        source_type:
            should be None; only when source_path or file.name doesnt deliver a correct file extension,
            then source_type should be '.json' or '.csv' for clarification
        file:
            should be None; only when a file is already loaded, it can be passed to file parameter
        """
        if file is not None:
            file_extension = None
            if source_type is None:
                _, file_extension = os.path.splitext(file.name)
            fr = FileReader(file=file, internal_call=True, show_printmessages=self.show_printmessages)
            file_load_method = fr.loadfile_types.get(source_type or file_extension)
        else:
            file_extension = None
            if source_type is None:
                _, file_extension = os.path.splitext(source_path)
            fr = FileReader(
                filepath=source_path, origin=origin, internal_call=True, show_printmessages=self.show_printmessages
            )
            file_load_method = fr.loadfile_types.get(source_type or file_extension)
        try:
            if file_load_method == ".csv":
                result = getattr(fr, file_load_method)(delimiting_character=csv_delimiter)
            else:
                result = getattr(fr, file_load_method)()
        except FileNotFound:
            print(
                f"EntityLibrary import_data_from_file_to_library() error: could not import new data from {source_path} to entity library, file not found"
            ) if self.show_printmessages == True else None
            return None
        except BadFormat:
            print(
                f"EntityLibrary import_data_from_file_to_library() error: could not import new data from {source_path} to entity library, bad format"
            ) if self.show_printmessages == True else None
            return None
        except MissingDefinition:
            print(
                f"EntityLibrary import_data_from_file_to_library() error: could not import new data from {source_path} to entity library, missing input parameter"
            ) if self.show_printmessages == True else None
            return None
        result = self.add_entities(result)
        return result

    def add_entities(
        self,
        data: List[dict] = None,
    ) -> Union[Tuple[int, int], str]:
        """method to add entities to library, which has been passed to function via data parameter;
        structure of data has to match the structure of self.data entities;
        data structure and redundancy checks are compulsory;
        test, if type string matches a type defined in link_sugesstion_categories.json, takes place in the GUI"""
        entity_amount_before_filtering = len(data)
        # check of data structure
        structure_check_cache = Cache(data=data)
        if structure_check_cache.check_json_structure("EntityLibrary") == False:
            print(
                f"Could not add entities to entity library, data does not fulfill the structure requirements. See documentation for requirement list."
            ) if self.show_printmessages else None
            return f"Could not add entities to entity library, data does not fulfill the structure requirements. See documentation for requirement list."
        # check for redundancy
        from_data_removed_entities = []
        for entity in reversed(data):
            redundancy_check_cache = Cache(data=self.data)
            redundancy_check_result = redundancy_check_cache.check_for_redundancy(
                "EntityLibrary", entity["wikidata_id"], entity["gnd_id"]
            )
            if any(redundancy_check_result):
                from_data_removed_entities.append(entity)
                data.remove(entity)
        from_data_removed_entities_amount = len(from_data_removed_entities)
        if from_data_removed_entities_amount > 0:
            print(
                f"The following {from_data_removed_entities_amount} entity/ies (from {entity_amount_before_filtering}) could not be added to entity library due to redundancy issues:"
            ) if self.show_printmessages == True else None
            print(from_data_removed_entities) if self.show_printmessages == True else None
        data_amount_after_filtering = len(data)
        if data_amount_after_filtering > 0:
            self.data.extend(data)
            print(
                f"{data_amount_after_filtering} entity/ies has/have been added to entity library."
            ) if self.show_printmessages == True else None
            return data_amount_after_filtering, from_data_removed_entities_amount
        else:
            print(
                f"None of the entities were added to entity library due to redundancy issues."
            ) if self.show_printmessages == True else None
            return f"None of the entities were added to entity library due to redundancy issues."

    def save_library(self) -> Union[bool, None]:
        """used to save current library data to the local json file with filepath self.data_file"""
        if self.data_file is None:
            print("EntityLibrary save_library() internal error: data_file parameter not defined")
            return False
            # raise MissingDefinition("data_file", "EntityLibrary", "save_library()")
        if self.data is None:
            print("EntityLibrary save_library() internal error: data parameter not defined")
            return False
            # raise MissingDefinition("data", "EntityLibrary", "save_library()")
        fw = FileWriter(data=self.data, filepath=self.data_file, show_printmessages=self.show_printmessages)
        try:
            result = fw.writefile_json("replace", "EntityLibrary")
        except MissingDefinition:
            print(
                "EntityLibrary save_library(): could not write file due to missing definition of usecase parameter"
            ) if self.show_printmessages == True else None
            result = None
        return result

    def export_library(
        self, file_type: str = ".csv", export_path: Union[str, None] = None, mode: str = "cancel"
    ) -> bool:
        """method to save currently loaded library data to export_path,
        supports .json and .csv file format

        file_type:
            selects file format to export to, can be '.json' or '.csv'
        export_path:
            file path to export data to
        mode:
            defines FileWriter`s behaviour in case the file in export_path already exists,
            can be 'cancel', 'replace' or 'merge'"""
        if file_type != ".csv" and file_type != ".json":
            print(
                "EntityLibrary export_library() internal error: file_type parameter not defined"
            ) if self.show_printmessages == True else None
            return False
            # raise MissingDefinition("file_type", "EntityLibrary", "export_library()")
        if export_path is None:
            print(
                "EntityLibrary export_library() internal error: file_type parameter not defined"
            ) if self.show_printmessages == True else None
            return False
            # raise MissingDefinition("export_path", "EntityLibrary", "export_library()")
        if self.data is None:
            print(
                "EntityLibrary export_library() internal error: data parameter not defined"
            ) if self.show_printmessages == True else None
            return False
            # raise MissingDefinition("data", "EntityLibrary", "export_library()")
        export_data = self.data if file_type == ".json" else None
        if export_data is None:
            pass
            # todo: write self.data to csv transformation
        fw = FileWriter(data=export_data, filepath=export_path, show_printmessages=self.show_printmessages)
        try:
            result = fw.writefile_types.get(file_type)(mode, "EntityLibrary")
        except MissingDefinition:
            print(
                "EntityLibrary export_library(): could not write file due to missing definition of mode and/or usecase parameter"
            ) if self.show_printmessages == True else None
            result = None
        return result

    def return_identification_suggestions_for_entity(
        self,
        input_entity: dict = None,
        try_to_identify_entities_without_id_values: bool = False,
        replace_furtherIds_information=False,
        wikidata_query_match_limit: str = "5",
    ) -> Union[Tuple[List[dict], int, str], Tuple[list, int, str]]:
        """method for postprocessing gui to get missing ids or identification suggestions for a single entity;
        returns tuple contains a list of entities, an integer value and a status message string;
        if the integer equals 0, then the identification suggestion is save and it can be saved or ignored without
        manually checking the result by user,
        if the integer equals -1, then the user has to choose if the suggested entity/entities should be added to entity library;
        if the returned list is empty, no suggestions was neccessary or could be made due to try_to_identify_entities_without_id_values parameter
        setting or a lack of matching data in wikidata database or due to an connection error"""

        # add missing furtherIds
        # todo: schalter: A auffüllen oder B ersetzen? (replace_furtherIds_information parameter einbauen)
        # todo: wenn A:
        # todo: self.furtherIds_config mit entity["furtherIds"] vergleichen: sind werte in den listen? (fehlende stellen in einer todo-Liste mit hostnamen einsammeln)
        # todo: wenn irgendwo was fehlt (todo-Liste hat einträge):
        # todo: 1. daten von wikidata und gnd api abrufen, entsprechend der furtherIds_config.json
        # todo: 2. datenbanken, zu denen werte fehlen, aus todo-liste auslesen
        # todo: 3. zu den benötigten Einträgen die Rückgabe-Werte von wikidata und gnd api zu einer diskreten Menge zusammenfügen (Dubletten entfernen)
        # todo: wenn B:
        # todo: daten von wikidata und gnd api abrufen, entsprechend der furtherIds_config.json, und das Ergebnis-dict in entity["furtherIds"] schreiben

        if (input_entity["wikidata_id"] == "") and (input_entity["gnd_id"] == ""):
            if try_to_identify_entities_without_id_values == False:
                return ([], 0, "entity ignored due to try_to_identify_entities_without_id_values parameter setting")
            else:
                input_tuple = (input_entity["name"], input_entity["type"])
                wikidata_connector = WikidataConnector(
                    input=[input_tuple], wikidata_web_api_limit=wikidata_query_match_limit
                )
                if input_entity["type"] not in list(wikidata_connector.link_suggestion_categories.keys()):
                    return ([], 0, "entity ignored due to missing or incorrect 'type' value")
                wikidata_connector_result = wikidata_connector.get_wikidata_search_results()
                if wikidata_connector_result[input_tuple][0] > 0:
                    entity_list_in_query_wikidata_result = []
                    for entity in wikidata_connector_result[input_tuple][1]["search"]:
                        _gnd_retrieve_attempt_result = self.get_gnd_id_of_wikidata_entity(entity["id"])
                        _gnd_id_to_add = (
                            _gnd_retrieve_attempt_result[0]["o"]["value"]
                            if len(_gnd_retrieve_attempt_result) > 0
                            else ""
                        )
                        _furtherNames_to_add = self.get_further_names_of_wikidata_entity(entity.get("id", ""))
                        _furtherIds_to_add = self.get_further_ids_of_wikidata_entity(entity.get("id", ""))
                        entity_list_in_query_wikidata_result.append(
                            {
                                "name": entity.get("label", f"No name delivered, search pattern was: {input_tuple[0]}"),
                                "furtherNames": _furtherNames_to_add,
                                "type": input_tuple[1],
                                "description": entity.get("description", "No description delivered"),
                                "wikidata_id": entity.get("id", ""),
                                "gnd_id": _gnd_id_to_add,
                                "furtherIds": _furtherIds_to_add,
                            }
                        )
                    return_value_len = len(entity_list_in_query_wikidata_result)
                    if return_value_len > 1:
                        return_value = (
                            entity_list_in_query_wikidata_result,
                            -1,
                            "multiple possible entities found in wikidata query",
                        )
                    elif return_value_len == 1:
                        return_value = (
                            entity_list_in_query_wikidata_result,
                            -1,
                            "one possible entity found in wikidata query",
                        )
                    elif return_value_len == 0:
                        return_value = (
                            entity_list_in_query_wikidata_result,
                            0,
                            "no possible entity found in wikidata query",
                        )
                    return return_value
                else:
                    return ([], 0, "no matching entities found in wikidata query")
        if (input_entity["wikidata_id"] != "") and (input_entity["gnd_id"] == ""):
            result_of_gnd_id_retrieval_attempt = self.get_gnd_id_of_wikidata_entity(input_entity["wikidata_id"])
            gnd_id_of_first_suggested_entity = (
                result_of_gnd_id_retrieval_attempt[0]["o"]["value"]
                if len(result_of_gnd_id_retrieval_attempt) > 0
                else ""
            )
            if gnd_id_of_first_suggested_entity != "":
                returned_entity = input_entity.copy()
                returned_entity["gnd_id"] = gnd_id_of_first_suggested_entity
                return ([returned_entity], 0, f"gnd_id {gnd_id_of_first_suggested_entity} determined")
            else:
                return ([], 0, "no id data could be retrieved for entity")
        if (input_entity["wikidata_id"] == "") and (input_entity["gnd_id"] != ""):
            gnd_connector = GndConnector(input_entity["gnd_id"])
            gnd_data = gnd_connector.get_gnd_data(["sameAs"])
            gnd_connector_sameAs_id_key = list(
                gnd_connector.apilist[gnd_connector.apiindex]["baseAliases"]["sameAs"][1][0].keys()
            )[0]
            filter_list_result = [
                item
                for item in gnd_data[input_entity["gnd_id"]]["sameAs"]
                if "http://www.wikidata.org/entity/" in item[gnd_connector_sameAs_id_key]
            ]
            if len(filter_list_result) == 1:
                from_gnd_api_retrieved_wikidata_id = filter_list_result[0][gnd_connector_sameAs_id_key][31:]
                returned_entity = input_entity.copy()
                returned_entity["wikidata_id"] = from_gnd_api_retrieved_wikidata_id
                return ([returned_entity], 0, f"wikidata_id {from_gnd_api_retrieved_wikidata_id} determined")
            else:
                return ([], 0, "no id data could be retrieved for entity")
        if (input_entity["wikidata_id"] != "") and (input_entity["gnd_id"] != ""):
            return ([], 0, "entity is already identified")

    def add_missing_id_numbers(
        self,
        add_first_suggested_wikidata_entity_if_no_id_was_given: bool = False,
        wikidata_query_match_limit: str = "5",
    ) -> Union[List[str], list]:
        """NOT IN USE AT THE MOMENT"""
        return_messages = []
        for entity in self.data:
            entity_unchanged = entity.copy()
            # add missing gnd_id or wikidata_id value
            if (entity["wikidata_id"] == "") and (entity["gnd_id"] == ""):
                if add_first_suggested_wikidata_entity_if_no_id_was_given == False:
                    return_messages.append(
                        f"{entity_unchanged} ignored due to add_first_suggested_wikidata_entity_if_no_id_was_given parameter setting"
                    )
                    continue
                else:
                    input_tuple = (entity["name"], entity["type"])
                    wikidata_connector = WikidataConnector(
                        input=[input_tuple], wikidata_web_api_limit=wikidata_query_match_limit
                    )
                    wikidata_connector_result = wikidata_connector.get_wikidata_search_results()
                    if wikidata_connector_result[input_tuple][0] > 0:
                        wikidata_id_of_first_suggested_entity = wikidata_connector_result[input_tuple][1]["search"][0][
                            "id"
                        ]
                        result_of_gnd_id_retrieval_attempt = self.get_gnd_id_of_wikidata_entity(
                            wikidata_id_of_first_suggested_entity
                        )
                        gnd_id_of_first_suggested_entity = (
                            result_of_gnd_id_retrieval_attempt[0]["o"]["value"]
                            if len(result_of_gnd_id_retrieval_attempt) > 0
                            else ""
                        )
                        # update self.data
                        entity["wikidata_id"] = wikidata_id_of_first_suggested_entity
                        entity["gnd_id"] = gnd_id_of_first_suggested_entity
                        return_messages.append(f"entity {entity_unchanged} changed to {entity}")
                    else:
                        return_messages.append(f"no id data could be retrieved for {entity_unchanged}")
                    continue
            if (entity["wikidata_id"] != "") and (entity["gnd_id"] == ""):
                result_of_gnd_id_retrieval_attempt = self.get_gnd_id_of_wikidata_entity(entity["wikidata_id"])
                gnd_id_of_first_suggested_entity = (
                    result_of_gnd_id_retrieval_attempt[0]["o"]["value"]
                    if len(result_of_gnd_id_retrieval_attempt) > 0
                    else ""
                )
                # update self.data
                entity["gnd_id"] = gnd_id_of_first_suggested_entity
                if gnd_id_of_first_suggested_entity != "":
                    return_messages.append(f"entity {entity_unchanged} changed to {entity}")
                else:
                    return_messages.append(f"no id data could be retrieved for {entity_unchanged}")
                continue
            if (entity["wikidata_id"] == "") and (entity["gnd_id"] != ""):
                gnd_connector = GndConnector(entity["gnd_id"])
                gnd_data = gnd_connector.get_gnd_data(["sameAs"])
                gnd_connector_sameAs_id_key = list(
                    gnd_connector.apilist[gnd_connector.apiindex]["baseAliases"]["sameAs"][1][0].keys()
                )[0]
                filter_list_result = [
                    item
                    for item in gnd_data[entity["gnd_id"]]["sameAs"]
                    if "http://www.wikidata.org/entity/" in item[gnd_connector_sameAs_id_key]
                ]
                if len(filter_list_result) == 1:
                    from_gnd_api_retrieved_wikidata_id = filter_list_result[0][gnd_connector_sameAs_id_key][31:]
                    entity["wikidata_id"] = from_gnd_api_retrieved_wikidata_id
                    return_messages.append(f"entity {entity_unchanged} changed to {entity}")
                else:
                    return_messages.append(f"no id data could be retrieved for {entity_unchanged}")
                continue
            if (entity["wikidata_id"] != "") and (entity["gnd_id"] != ""):
                return_messages.append(f"no id data had to be retrieved for {entity_unchanged}")
                continue
        return return_messages

    def get_gnd_id_of_wikidata_entity(self, wikidata_id: str):
        """method to get gnd id number for a given wikidata id by sparql query,
        p227 = gnd id"""
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
        # if there is no result, the returned value is an empty list
        # if there is a result, it can be retrieved by returnvalue[0]["o"]["value"]

    def get_further_names_of_wikidata_entity(self, wikidata_id: str = None) -> List[str]:
        """method to get further names of a wikidata entity,
        returns a list for a furtherName value of an entity library entity dict,
        origin of the information are the properties rdfs:label and skos:altLabel"""
        if wikidata_id == "":
            return []
        alt_labels_query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

            SELECT ?label WHERE {
                VALUES ?p { rdfs:label skos:altLabel } 
                wd:%s ?p ?label .
            }
        """
        endpoint_url = "https://query.wikidata.org/sparql"
        user_agent = "NEISS TEI Entity Enricher v.{}".format(__version__)
        sparql = SPARQLWrapper(endpoint=endpoint_url, agent=user_agent)
        sparql.setQuery(alt_labels_query % wikidata_id)
        sparql.setReturnFormat(JSON)
        query_result = sparql.query().convert()
        # return empty list, if no result is returned by sparql query
        if len(query_result["results"]["bindings"]) == 0:
            return []
        # return a list with distinct values: for this, the list is transformed to a set and back to new list without value doublets
        return list(set([item["label"]["value"] for item in query_result["results"]["bindings"]]))

    def get_further_names_of_gnd_entity(self, gnd_id: str = None) -> List[str]:
        """method to get further names of a gnd entity,
        returns a list for a furtherName value of an entity library entity dict,
        origin of the information is the database related to the gnd api choosen in gndConnector object

        NOT IN USE AT THE MOMENT"""
        if gnd_id == "":
            return []
        gnd_connector = GndConnector(gnd_id)
        query_result = gnd_connector.get_gnd_data(["furtherNames"])
        return query_result[gnd_id]["furtherNames"]

    def get_further_ids_of_wikidata_entity(self, wikidata_id: str = None) -> dict:
        """method to get further ids of a wikidata entity, retrieving entity ids from databases defined in self.furtherIds_config,
        returns a dict which can be used as value for furtherId key in entity library entity dicts,
        information are retrieved from wikidata sparql endpoint on the basis of the properties defined in self.furtherIds_config

        output example for 'Berlin': {"geonames.com": ["2950159", "2950157", "6547383", "6547539"], "viaf.org": ["122530980"]}
        """
        if wikidata_id == "":
            return []
        endpoint_url = "https://query.wikidata.org/sparql"
        user_agent = "NEISS TEI Entity Enricher v.{}".format(__version__)
        further_ids_query = """
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>

            SELECT ?label WHERE {
            VALUES ?p { %s } 
            wd:%s ?p ?label .
            }
        """
        result_dict = {key: [] for key in self.furtherIds_config}
        for key in self.furtherIds_config:
            sparql = SPARQLWrapper(endpoint=endpoint_url, agent=user_agent)
            sparql.setQuery(further_ids_query % (self.furtherIds_config[key][0], wikidata_id))
            sparql.setReturnFormat(JSON)
            query_result = sparql.query().convert()
            for query_result_item in query_result["results"]["bindings"]:
                result_dict[key].append(query_result_item["label"]["value"])
        return result_dict

    def get_further_ids_of_gnd_entity(self, gnd_id: str = None) -> List[str]:
        """method to get further ids of a gnd entity,
        returns a dict for a furtherIds value of an entity library entity dict,
        keys are the hostnames of the urls provided by query, values are the complete uris,
        origin of the information is the database related to the gnd api choosen in gndConnector object

        NOT IN USE AT THE MOMENT"""
        if gnd_id == "":
            return []
        gnd_connector = GndConnector(gnd_id)
        gnd_connector_sameAs_id_key = list(
            gnd_connector.apilist[gnd_connector.apiindex]["baseAliases"]["sameAs"][1][0].keys()
        )[0]
        query_result = gnd_connector.get_gnd_data(["sameAs"])
        uri_list = [
            item[gnd_connector_sameAs_id_key]
            for item in query_result[gnd_id]["sameAs"]
            if "https://d-nb.info/gnd" not in item[gnd_connector_sameAs_id_key]
            if "wikipedia.org" not in item[gnd_connector_sameAs_id_key]
            if "wikisource.org" not in item[gnd_connector_sameAs_id_key]
            if "wikidata.org" not in item[gnd_connector_sameAs_id_key]
        ]
        uri_dict = {urlparse(i).hostname: i for i in uri_list}
        return uri_dict

    def reset(self):
        self.data_file = None
        self.use_default_data_file = False
        self.show_printmessages = True
        self.data_file = None
        self.data = None
