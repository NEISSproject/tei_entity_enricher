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
        which is used as data source for named entity identification in post-processing and for optimizing
        the named entity recognition process

        it can be build up manually or inside an identification pipeline, where wikidata entity search results
        can be enriched by gnd database Connector and added to EntityLibrary

        data_file: path to json file, from which data is loaded and to which the data should be saved to
        show_printmessages: show class internal printmessages on runtime or not
        data: currently loaded dict, is loaded from json file on __init__(), if a filepath in data_file is provided
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
        """used to load library data from a local json file with filepath saved in self.data_file,
        depending on file extension of self.data_file the correct method of FileReader is choosen
        by getting the attribute via loadfile_types dict of FileReader class"""
        if self.data_file is None:
            print("EntityLibrary load_library() Error: data_file parameter not defined")
            return False
        fr = FileReader(self.data_file, "local", True, self.show_printmessages)
        _, file_extension = os.path.splitext(self.data_file)
        result = getattr(fr, fr.loadfile_types.get(file_extension))()
        return result

        # file found, but no valid data: FileReader returns None
        # file not found: FileReader returns None

    def save_library(self) -> bool:
        """used to save library data to a local json file with filepath saved in self.data_file"""
        # todo: get correct FileWriter method depending on file extension of self.data_file
        if self.data_file is None:
            print("EntityLibrary save_library() Error: data_file parameter not defined")
            return False
        if self.data is None:
            print("EntityLibrary save_library() Error: data parameter not defined")
            return False
        fw = FileWriter(self.data, self.data_file, self.show_printmessages)
        return fw.writefile_json("replace")
