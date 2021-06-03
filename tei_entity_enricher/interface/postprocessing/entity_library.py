from typing import Union, List
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter, Cache
from tei_entity_enricher.util.helper import local_save_path, makedir_if_necessary
from tei_entity_enricher.util.exceptions import MissingDefinition, FileNotFound, BadFormat
import os


class EntityLibrary:
    def __init__(
        self,
        data_file: Union[str, None] = os.path.join(local_save_path, "config", "postprocessing", "entity_library.json"),
        show_printmessages: bool = True,
    ) -> None:
        """is a runtime memory of entities (saved properties are: name, furtherNames, type, gnd_id, wikidata_id),
        which is used as data source for named entity identification in post-processing

        it can be build up manually or inside an identification pipeline, where wikidata entity search results
        can be enriched by data retrieved by GndConnector and alltogether added to EntityLibrary

        data_file:
            path to json file, from which data is loaded and to which the data should be saved to
        show_printmessages:
            show class internal printmessages on runtime or not
        data:
            currently loaded dict, is loaded from json file on __init__(), if a correct filepath in data_file is provided
        """
        self.data_file: Union[str, None] = data_file
        self.show_printmessages: bool = show_printmessages
        self.data: Union[list, None] = None
        if self.data_file is not None:
            if self.load_library() == True:
                print(f"EntityLibrary loaded from {self.data_file}...") if self.show_printmessages else None
        else:
            print("EntityLibrary initialized without data...") if self.show_printmessages else None

    def load_library(self) -> bool:
        """used to load existing library data from a local json file with filepath saved in self.data_file"""
        if self.data_file is None:
            raise MissingDefinition("data_file", "EntityLibrary", "load_library()")
        fr = FileReader(self.data_file, "local", True, self.show_printmessages)
        result = None
        try:
            result = fr.loadfile_json()
        except FileNotFound:
            print(
                f"EntityLibrary load_library(): could not load library from {self.data_file}, file not found. creating default library file..."
            ) if self.show_printmessages else None
            try:
                makedir_if_necessary(os.path.dirname(self.data_file))
                FileWriter(
                    [{"name": "", "furtherNames": [], "type": "", "wikidata_id": "", "gnd_id": ""}], self.data_file
                ).writefile_json()
            except:
                print(
                    f"EntityLibrary load_library(): could not create default entity_library.json in config folder."
                ) if self.show_printmessages == True else None
                return False
            result = fr.loadfile_json()
        except BadFormat:
            print(
                f"EntityLibrary load_library(): could not load library from {self.data_file}, no valid json format."
            ) if self.show_printmessages else None
            return False
        structure_check_cache = Cache(result)
        if structure_check_cache.check_json_structure("EntityLibrary") == False:
            print(
                f"EntityLibrary load_library(): could not load library from {self.data_file}, file does not fulfill the structure requirements for EntityLibrary. See documentation for requirement list."
            ) if self.show_printmessages else None
            return False
        self.data = result
        return True

    def add_entities_from_file(
        self, source_path: str = None, origin: str = "local", source_type: str = None
    ) -> Union[None, int]:
        """used to add data from source (json or csv format) into the already loaded entity library

        source_path:
            uri or filepath in local system to source, from which entities should be added to library
        origin:
            source setting for used FileReader, can be 'web' or 'local'
        source_type:
            should be None; only when source_path doesnt deliver a correct file extension,
            then source_type should be '.json' or '.csv' for clarification
        """
        file_extension = None
        if source_type is None:
            _, file_extension = os.path.splitext(source_path)
        fr = FileReader(source_path, origin, True, self.show_printmessages)
        file_load_method = fr.loadfile_types.get(source_type or file_extension)
        try:
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
        self.add_entities(result)

    def add_entities(
        self,
        data: List[dict] = None,
    ) -> Union[int, None]:
        """method to add entities to library, which has been passed to function via data parameter;
        structure of data has to match the structure of self.data entities;
        data structure and redundancy checks are compulsory"""
        entity_amount_before_filtering = len(data)
        # check of data structure
        structure_check_cache = Cache(data)
        if structure_check_cache.check_json_structure("EntityLibrary") == False:
            print(
                f"EntityLibrary add_entities(): could not add entities to entity library, data does not fulfill the structure requirements for EntityLibrary. See documentation for requirement list."
            ) if self.show_printmessages else None
            return -1
        # check for redundancy
        from_data_removed_entities = []
        for entity in data:
            redundancy_check_cache = Cache(self.data)
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
            return 0
        else:
            print(f"No entities have been added to entity library.") if self.show_printmessages == True else None
            return -1

    def save_library(self) -> bool:
        """used to save current library data to the local json file with filepath self.data_file"""
        if self.data_file is None:
            print("EntityLibrary save_library() internal error: data_file parameter not defined")
            return False
            # raise MissingDefinition("data_file", "EntityLibrary", "save_library()")
        if self.data is None:
            print("EntityLibrary save_library() internal error: data parameter not defined")
            return False
            # raise MissingDefinition("data", "EntityLibrary", "save_library()")
        fw = FileWriter(self.data, self.data_file, self.show_printmessages)
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
            print("EntityLibrary export_library() internal error: file_type parameter not defined")
            return False
            # raise MissingDefinition("file_type", "EntityLibrary", "export_library()")
        if export_path is None:
            print("EntityLibrary export_library() internal error: file_type parameter not defined")
            return False
            # raise MissingDefinition("export_path", "EntityLibrary", "export_library()")
        if self.data is None:
            print("EntityLibrary export_library() internal error: data parameter not defined")
            return False
            # raise MissingDefinition("data", "EntityLibrary", "export_library()")
        export_data = self.data if file_type == ".json" else None
        if export_data is None:
            pass
            # todo: write self.data to csv transformation
        fw = FileWriter(export_data, export_path, self.show_printmessages)
        try:
            result = fw.writefile_types.get(file_type)(mode, "EntityLibrary")
        except MissingDefinition:
            print(
                "EntityLibrary export_library(): could not write file due to missing definition of mode and/or usecase parameter"
            ) if self.show_printmessages == True else None
            result = None
        return result
