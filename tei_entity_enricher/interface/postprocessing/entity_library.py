from typing import Union, List, Tuple
from streamlit.uploaded_file_manager import UploadedFile
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter, Cache
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector
from tei_entity_enricher.interface.postprocessing.gnd_connector import GndConnector
from tei_entity_enricher.util.helper import local_save_path, makedir_if_necessary
from tei_entity_enricher.util.exceptions import MissingDefinition, FileNotFound, BadFormat
import os
from tei_entity_enricher import __version__
from SPARQLWrapper import SPARQLWrapper, JSON


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
        """
        self.use_default_data_file: bool = use_default_data_file
        self.default_data_file: str = os.path.join(local_save_path, "config", "postprocessing", "entity_library.json")
        self.data_file: Union[str, None] = self.default_data_file if self.use_default_data_file == True else data_file
        self.show_printmessages: bool = show_printmessages
        self.data: Union[list, None] = None
        if (self.data_file is not None) and (self.load_library() == True):
            print(f"EntityLibrary loaded from {self.data_file}...") if self.show_printmessages else None
        else:
            print("EntityLibrary initialized without data...") if self.show_printmessages else None

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
                                "name": "",
                                "furtherNames": [],
                                "type": "",
                                "description": "",
                                "wikidata_id": "",
                                "gnd_id": "",
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
        data structure and redundancy checks are compulsory"""
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

    def add_missing_id_numbers(self, add_first_suggested_wikidata_entity_if_no_id_was_given: bool = False) -> List[str]:
        return_messages = []
        for entity in self.data:
            entity_unchanged = entity.copy()
            if (entity["wikidata_id"] == "") and (entity["gnd_id"] == ""):
                if add_first_suggested_wikidata_entity_if_no_id_was_given == False:
                    return_messages.append(
                        f"{entity_unchanged} ignored due to add_first_suggested_wikidata_entity_if_no_id_was_given parameter setting"
                    )
                    continue
                else:
                    input_tuple = (entity["name"], entity["type"])
                    wikidata_connector = WikidataConnector([input_tuple])
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
                filter_list_result = list(
                    filter(
                        lambda item: "http://www.wikidata.org/entity/" in item["@id"],
                        gnd_data[entity["gnd_id"]]["sameAs"],
                    )
                )
                if len(filter_list_result) == 1:
                    from_gnd_api_retrieved_wikidata_id = filter_list_result[0]["@id"][31:]
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

    def reset(self):
        self.data_file = None
        self.use_default_data_file = False
        self.show_printmessages = True
        self.data_file = None
        self.data = None
