from typing import Union
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter
from tei_entity_enricher.util.helper import local_save_path
import os


class EntityLibrary:
    def __init__(
        self,
        data_file: Union[str, None] = os.path.join(local_save_path, "config", "postprocessing", "entity_library.json"),
        show_printmessages: bool = True,
    ) -> None:
        """is a memory of entities (saved properties are: name, furtherNames, type, gnd_id, wikidata_id),
        which is used as data source for named entity identification in post-processing

        it can be build up manually or inside an identification pipeline, where wikidata entity search results
        can be enriched by data retrieved by GndConnector and added to EntityLibrary

        data_file: path to json file, from which data is loaded and to which the data should be saved to
        show_printmessages: show class internal printmessages on runtime or not
        data: currently loaded dict, is loaded from json file on __init__(), if a correct filepath in data_file is provided
        """
        self.data_file: Union[str, None] = data_file
        self.show_printmessages: bool = show_printmessages

        # HIER WEITER: differentiation of file extension necessary? create dir and file if not existent

        if self.data_file is not None:
            self.data: Union[dict, None, bool] = self.load_library()
            print(f"EntityLibrary loaded from {self.data_file}...") if self.show_printmessages else None
        else:
            self.data: Union[dict, None, bool] = None
            print("EntityLibrary initialized without data...") if self.show_printmessages else None

    def load_library(self) -> Union[dict, None, bool]:
        """used to load existing library data from a local json file with filepath saved in self.data_file"""
        if self.data_file is None:
            print("EntityLibrary load_library() internal error: data_file parameter not defined")
            return False
        fr = FileReader(self.data_file, "local", True, self.show_printmessages)
        result = fr.loadfile_json()
        return result

        # file found, but no valid data: FileReader returns None
        # file not found: FileReader returns None

    def import_data_to_library(
        self, source_path: str = None, origin: str = None, source_type: str = None, mode="merge"
    ) -> Union[None, int]:
        """used to add data from source (json or csv format) into the already loaded entity library

        source_path: uri or filepath in local system
        origin: 'web' or 'local'
        source_type: should be None; only when source_path doesnt deliver a correct file extension,
        then source_type should be '.json' or '.csv' for clarification
        mode: can be 'cancel', 'replace' or 'merge' (categories correspond to modi of FileWriter`s writefile_json())
        """
        file_extension = None
        if source_type is None:
            _, file_extension = os.path.splitext(source_path)
        fr = FileReader(source_path, origin, True, self.show_printmessages)
        result = getattr(fr, fr.loadfile_types.get(source_type or file_extension))()
        # todo: merge result in self.data

    def save_library(self) -> bool:
        """used to save library data to a local json file with filepath self.data_file"""
        if self.data_file is None:
            print("EntityLibrary save_library() internal error: data_file parameter not defined")
            return False
        if self.data is None:
            print("EntityLibrary save_library() internal error: data parameter not defined")
            return False
        fw = FileWriter(self.data, self.data_file, self.show_printmessages)
        return fw.writefile_json("replace")

    def export_library(
        self, file_type: str = ".csv", export_path: Union[str, None] = None, mode: str = "cancel"
    ) -> bool:
        """method to save currently loaded library data to export_path,
        supports .json and .csv file format

        file_type: selects file format to export to
        export_path: file path to export data to"""
        if file_type != ".csv" and file_type != ".json":
            print("EntityLibrary export_library() internal error: file_type parameter not defined")
            return False
        if export_path is None:
            print("EntityLibrary export_library() internal error: file_type parameter not defined")
            return False
        if self.data is None:
            print("EntityLibrary export_library() internal error: data parameter not defined")
            return False
        export_data = self.data if file_type == ".json" else None
        if export_data is None:
            pass
            # todo: write transformation
        fw = FileWriter(export_data, export_path, self.show_printmessages)
        return fw.writefile_json(mode)
