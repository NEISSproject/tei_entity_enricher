import streamlit as st
import logging
import json
import os

from streamlit_ace import st_ace
from typing import Union
from math import floor, trunc
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter, Cache
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector
from tei_entity_enricher.util.exceptions import BadFormat
import tei_entity_enricher.menu.tei_man_postproc as tmp
from tei_entity_enricher.util.helper import (
    state_failed,
    state_ok,
    transform_arbitrary_text_to_markdown,
    local_save_path,
    makedir_if_necessary,
)

logger = logging.getLogger(__name__)

# auxiliary cache definition
class PostprocessingAuxiliaryCache:
    """class to save different states over streamlit reruns
    el_filepath : str
        filepath to entity library, which is loaded or should be loaded
    last_editor_state : str
        ace editor state of the last run, used to be able to compare old and current ace editor state
    button_add_missing_ids : bool
        saves was-pressed state over more than one rerun
    button_add_missing_ids_proceed : bool
        saves was-pressed state over more than one rerun
    button_export_el : bool
        saves was-pressed state over more than one rerun
    add_missing_ids_query_result : dict
        saves temporarily wikidata query result in add-missing-ids process
    counter : int
        used to change ace editor key value between two reruns, if self.is_count_up_rerun is True
    is_count_up_rerun : bool
        used to control, if counter is raised in a rerun (ace editor can be updated by internal processes) or not (ace editor can be changed manually)
    """

    def __init__(self) -> None:
        self.el_filepath: str = None
        self.last_editor_state: str = None
        self.button_add_missing_ids: bool = False
        self.button_add_missing_ids_proceed: bool = False
        self.button_export_el: bool = False
        self.add_missing_ids_query_result: dict = {}
        self.counter: int = 0
        self.is_count_up_rerun: bool = False

    def reset_buttons(self) -> None:
        self.button_add_missing_ids: bool = False
        self.button_add_missing_ids_proceed: bool = False
        self.button_export_el: bool = False

    def reset_filepath(self) -> None:
        self.el_filepath = None

    def reset_editor_state(self) -> None:
        self.last_editor_state: str = None

    def reset_add_missing_ids_query_result(self) -> None:
        self.add_missing_ids_query_result: dict = {}

    def reset_is_count_up_rerun(self) -> None:
        self.is_count_up_rerun: bool = False

    def set_el_filepath(self, path) -> None:
        self.el_filepath: str = path


# put/load entity library and auxiliary cache class instances in/from cache
@st.cache(allow_output_mutation=True)
def get_entity_library():
    return EntityLibrary(show_printmessages=False)


@st.cache(allow_output_mutation=True)
def get_pp_auxiliary_cache():
    return PostprocessingAuxiliaryCache()


# auxiliary functions
def el_editor_content_check(ace_editor_content: str) -> Union[bool, str]:
    """checks for content of ace editor;
    returns string if a check fails"""
    # valid json check
    fr = FileReader(file=ace_editor_content, internal_call=True, show_printmessages=False)
    try:
        fr_result = fr.loadfile_json()
    except BadFormat:
        return "Editor content is no valid json."
    # valid entity library check
    ca = Cache(fr_result)
    ca_el_structure_result = ca.check_json_structure(usecase="EntityLibrary")
    if ca_el_structure_result == False:
        return "Editor content does not fulfill the structure requirements for EntityLibrary. See documentation for requirement list."
    wcon = WikidataConnector(check_connectivity=False, show_printmessages=False)
    for e in fr_result:
        if e["type"] not in list(wcon.wikidata_sparql_queries.keys()):
            return f"An entity ({e['name']}) in editor content is missing a valid 'type' value"
    # redundancy check
    ca_el_redundancy_result = True
    for entity in ca.data:
        data_without_entity = [i for i in ca.data if not (i == entity)]
        _temp_cache = Cache(data_without_entity)
        _temp_ca_el_redundancy_result_tuple = _temp_cache.check_for_redundancy(
            usecase="EntityLibrary", wikidata_id=entity["wikidata_id"], gnd_id=entity["gnd_id"]
        )
        if any(_temp_ca_el_redundancy_result_tuple):
            ca_el_redundancy_result = False
            break
    if ca_el_redundancy_result == False:
        return "Editor content contains a redundancy issue; a wikidata or gnd id is assigned to more than one entity."
    return True


def frange_positve(start, stop=None, step=None):
    """equivalent function to pythons range(), but for float values"""
    if stop == None:
        stop = start + 0.0
        start = 0.0
    if step == None:
        step = 1.0
    count = 0
    while True:
        temp = float(start + count * step)
        if temp >= stop:
            break
        yield temp
        count += 1


def fix_editor_content(content):
    """workaround for ace editor bug: editor content is stringified multiple times,
    so that a single json.loads() execution returns a string and not a dict"""
    while type(json.loads(content)) == str:
        content = json.loads(content)
    return content


class TEINERPostprocessing:
    def __init__(self,show_menu: bool = True):
        """consists of the entity library control panel and the manual postprocessing panel"""
        if show_menu:
            self.init_vars()
            self.show()

    def init_vars(self):
        self.pp_el_library_object: EntityLibrary = get_entity_library()
        self.pp_aux_cache: PostprocessingAuxiliaryCache = get_pp_auxiliary_cache()
        self.pp_aux_cache.set_el_filepath(
            self.pp_el_library_object.default_data_file
        ) if self.pp_aux_cache.el_filepath is None else None

    def filepath_subcontainer(self):
        self.el_filepath_container = st.container()
        with self.el_filepath_container:
            self.el_filepath_field_col, self.el_filepath_state_col = st.columns([10, 1])
            self.el_filepath_field = self.el_filepath_field_col.text_input(
                label="Filepath to load from",
                value=self.pp_aux_cache.el_filepath,
                help="Enter the filepath to a json file, from which the entity library is loaded.",
            )
            self.el_create_filepath_if_not_found_checkbox = st.checkbox(
                label="Create default file if not found?",
                value=False,
                help="If selected, a default library file will be created in the given filepath.",
            )
            (
                self.el_col_init_button,
                self.el_col_quit_button,
                self.el_col_save_button,
                self.el_col_export_button,
                self.el_col_add_missing_ids_button,
            ) = st.columns(5)
            with self.el_col_init_button:
                self.el_init_button_placeholder = st.empty()
            with self.el_col_quit_button:
                self.el_quit_button_placeholder = st.empty()
            with self.el_col_save_button:
                self.el_save_button_placeholder = st.empty()
            with self.el_col_export_button:
                self.el_export_button_placeholder = st.empty()
            with self.el_col_add_missing_ids_button:
                self.el_add_missing_ids_button_placeholder = st.empty()
            self.el_init_button = self.el_init_button_placeholder.button(
                label="Initialize", key="init", help="Initialize the library from filepath."
            )
            self.el_quit_button = self.el_quit_button_placeholder.button(
                label="Unload", help="Unload the current library (unsaved changes will be lost)."
            )
            self.el_save_button = self.el_save_button_placeholder.button(
                label="Save", help="Save the current library state to filepath."
            )
            self.el_export_button = self.el_export_button_placeholder.button(
                label="Export", help="Export the current library state to another filepath."
            )
            self.el_add_missing_ids_button = self.el_add_missing_ids_button_placeholder.button(
                label="Add missing IDs",
                help="If an ID is missing in any entity, it will be retrieved on basis of the given information. If no id is given at all, an item of a list of suggestions delivered by wikidata query can be chosen.",
            )
            self.el_export_filepath_placeholder = st.empty()
            self.el_add_missing_ids_menu_placeholder = st.empty()
            self.el_init_message_placeholder = st.empty()
            self.el_misc_message_placeholder = st.empty()
            self.el_file_view_placeholder = st.empty()
            self.el_file_view_message_placeholder = st.empty()

    def add_entities_from_file_subcontainer_and_processes(self):
        self.el_add_entities_from_file_subcontainer = st.container()
        with self.el_add_entities_from_file_subcontainer:
            self.el_add_entities_from_file_loader_placeholder = st.empty()
            self.el_add_entities_from_file_button_placeholder = st.empty()
            self.el_add_entities_from_file_success_message_placeholder = st.empty()
            # processes triggered if an entity library is loaded (and it has a string value in data_file)
            if self.pp_el_library_object.data_file is not None:
                self.el_add_entities_from_file_loader_file_list = self.el_add_entities_from_file_loader_placeholder.file_uploader(
                    label="Add entities from file",
                    type=["json", "csv"],
                    accept_multiple_files=True,
                    key=None,
                    help="Use json or csv files to add entities to the loaded library. Importing multiple files at once is possible, see the documentation for file structure requirements.",
                )
                if len(self.el_add_entities_from_file_loader_file_list) > 0:
                    self.el_add_entities_from_file_button_value = (
                        self.el_add_entities_from_file_button_placeholder.button(
                            label="Start adding process", key=None, help=None
                        )
                    )
                    # processes triggered by add entities button
                    if self.el_add_entities_from_file_button_value == True:
                        result_messages = []
                        for uploaded_file in self.el_add_entities_from_file_loader_file_list:
                            el_add_entities_from_file_single_file_result = (
                                self.pp_el_library_object.add_entities_from_file(file=uploaded_file)
                            )
                            logger.info(
                                f"add_entities_from_file() result for {uploaded_file.name}: {el_add_entities_from_file_single_file_result}."
                            )
                            if type(el_add_entities_from_file_single_file_result) == str:
                                result_messages.append(
                                    f"{uploaded_file.name}: {el_add_entities_from_file_single_file_result}"
                                )
                            else:
                                result_messages.append(
                                    f"{uploaded_file.name}: {el_add_entities_from_file_single_file_result[0]} entity/ies successfully added to entity library. {el_add_entities_from_file_single_file_result[1]} entity/ies ignored due to redundance issues."
                                )
                            with self.el_add_entities_from_file_success_message_placeholder.container():
                                for message in result_messages:
                                    if "success" in message:
                                        st.success(message)
                                    else:
                                        st.info(message)
                        self.pp_aux_cache.last_editor_state = json.dumps(self.pp_el_library_object.data, indent=4)
                        self.pp_aux_cache.is_count_up_rerun = True
                        st.button(label="Finish process")

    def submenu_control(self):
        if (
            self.el_quit_button == True
            or self.el_save_button == True
            or self.el_export_button == True
            or self.el_add_missing_ids_button == True
        ):
            self.pp_aux_cache.reset_buttons()

    def init_button_processes(self):
        with self.el_filepath_container:
            if self.el_init_button == True:
                if self.pp_el_library_object.data_file is None:
                    self.pp_el_library_object.data_file = self.el_filepath_field
                    load_attempt_result = self.pp_el_library_object.load_library(
                        self.el_create_filepath_if_not_found_checkbox
                    )
                    if load_attempt_result == True:
                        logger.info(f"Entity library loading process from file {self.el_filepath_field} succeeded.")
                        self.pp_aux_cache.el_filepath = self.el_filepath_field
                    elif type(load_attempt_result) == str:
                        load_attempt_result = transform_arbitrary_text_to_markdown(load_attempt_result)
                        logger.warning(f"Entity library loading process failed: {load_attempt_result}")
                        self.el_filepath_state_col.latex(state_failed)
                        self.el_init_message_placeholder.error(load_attempt_result)
                        self.pp_el_library_object.data_file = None

    def save_button_processes(self):
        with self.el_filepath_container:
            if self.el_save_button == True:
                if self.pp_el_library_object.data_file is not None:
                    save_attempt_result = self.pp_el_library_object.save_library()
                    if save_attempt_result == True:
                        self.el_misc_message_placeholder.success(
                            "The current state of the entity library was successfully saved."
                        )
                    else:
                        self.el_misc_message_placeholder.error("Could not save current state of entity library.")
                    self.pp_aux_cache.reset_buttons()
                    self.pp_aux_cache.reset_add_missing_ids_query_result()

    def export_button_processes(self):
        with self.el_filepath_container:
            if self.el_export_button == True or self.pp_aux_cache.button_export_el == True:
                if self.pp_el_library_object.data_file is not None:
                    self.pp_aux_cache.button_export_el = True
                    el_export_filepath_field_container = self.el_export_filepath_placeholder.container()
                    el_export_filepath_field = el_export_filepath_field_container.text_input(
                        label="Filepath to export to",
                        value=os.path.join(local_save_path, "config", "postprocessing", "export.json"),
                        help="Enter the filepath to a json file, to which the entity library should be exported.",
                    )
                    el_export_create_folder_checkbox = el_export_filepath_field_container.checkbox(
                        label="Create folder if not found?",
                        value=True,
                        help="If selected, possibly not existant folders will be created according to the entered filepath value.",
                    )
                    el_export_overwrite_checkbox = el_export_filepath_field_container.checkbox(
                        label="Overwrite possibly existing file?",
                        value=False,
                        help="If selected, the file will be overwritten, if one already exists in filepath.",
                    )
                    proceed_button = el_export_filepath_field_container.button(
                        label="Proceed", help="Start export process."
                    )
                    if proceed_button == True:
                        fw = FileWriter(data=self.pp_el_library_object.data, filepath=el_export_filepath_field)
                        if_file_exists = "replace" if el_export_overwrite_checkbox == True else "cancel"
                        if el_export_create_folder_checkbox == True:
                            makedir_if_necessary(os.path.dirname(el_export_filepath_field))
                        try:
                            fw_return_value = fw.writefile_json(do_if_file_exists=if_file_exists)
                        except FileNotFoundError:
                            fw_return_value = "folder_not_found"
                        if fw_return_value == True:
                            self.el_misc_message_placeholder.success("Entity Library successfully exported.")
                        elif fw_return_value == False:
                            self.el_misc_message_placeholder.info("Entity Library export failed: File already exists.")
                        elif fw_return_value == "folder_not_found":
                            self.el_misc_message_placeholder.info(
                                "Entity Library export failed: Folder does not exist."
                            )

    def quit_button_processes(self):
        with self.el_filepath_container:
            if self.el_quit_button == True:
                if self.pp_el_library_object.data_file is not None:
                    self.pp_el_library_object.reset()
                    self.pp_aux_cache.reset_filepath()
                    self.pp_aux_cache.reset_editor_state()
                    self.pp_aux_cache.reset_buttons()
                    self.pp_aux_cache.reset_add_missing_ids_query_result()

    def add_missing_ids_button_processes(self):
        with self.el_filepath_container:
            if self.el_add_missing_ids_button == True or self.pp_aux_cache.button_add_missing_ids == True:
                if self.pp_el_library_object.data_file is not None:
                    self.pp_aux_cache.button_add_missing_ids = True
                    with self.el_add_missing_ids_menu_placeholder.container():
                        progress_bar = st.progress(0)
                        checkbox_state = st.checkbox(
                            label="Try to identify entities without any ids",
                            value=False,
                            help="When activated, for every entity in entity library, which has no id data at all, a list of matching entities in wikidata database will be suggested.",
                        )
                        if checkbox_state == True:
                            wikidata_search_amount = st.number_input(
                                label="max number of query results",
                                min_value=1,
                                max_value=50,
                                value=5,
                                step=1,
                                help="Choose the maximum number of results the wikidata query can deliver.",
                            )
                        else:
                            wikidata_search_amount = 5
                        proceed_button = st.button(
                            label="Query",
                            help="Start process, in which ids will be suggested for the entities in entity library.",
                        )
                        if proceed_button == True or self.pp_aux_cache.button_add_missing_ids_proceed == True:
                            self.pp_aux_cache.button_add_missing_ids_proceed = True
                            cases_to_ignore = []
                            identified_cases = []
                            cases_to_choose = []
                            selectbox_result = []
                            if len(self.pp_aux_cache.add_missing_ids_query_result) > 0:
                                # load wikidata query results from cache, if they exist
                                cases_to_ignore = self.pp_aux_cache.add_missing_ids_query_result["cases_to_ignore"]
                                identified_cases = self.pp_aux_cache.add_missing_ids_query_result["identified_cases"]
                                cases_to_choose = self.pp_aux_cache.add_missing_ids_query_result["cases_to_choose"]
                                progress_bar.progress(100)
                            else:
                                # wikidata query
                                library_data_length = len(self.pp_el_library_object.data)
                                progress_amount = floor((100 / library_data_length) * 10 ** 2) / 10 ** 2
                                progress_amount_list = list(frange_positve(0, 100, progress_amount))
                                for index, entity in enumerate(self.pp_el_library_object.data):
                                    _temp_result_entity_identification = (
                                        self.pp_el_library_object.return_identification_suggestions_for_entity(
                                            input_entity=entity,
                                            try_to_identify_entities_without_id_values=checkbox_state,
                                            wikidata_query_match_limit=str(wikidata_search_amount),
                                        )
                                    )
                                    current_progress_state = progress_amount_list[index]
                                    progress_val = trunc(current_progress_state + progress_amount)
                                    if progress_val > 100:
                                        progress_val = 100
                                    progress_bar.progress(trunc(current_progress_state + progress_amount))
                                    _len_temp_result = len(_temp_result_entity_identification[0])
                                    if _len_temp_result == 0:
                                        cases_to_ignore.append(_temp_result_entity_identification)
                                    elif _len_temp_result == 1:
                                        if _temp_result_entity_identification[1] == 0:
                                            identified_cases.append((_temp_result_entity_identification, index))
                                        else:
                                            cases_to_choose.append((_temp_result_entity_identification, index))
                                    elif _len_temp_result > 1:
                                        cases_to_choose.append((_temp_result_entity_identification, index))
                                self.pp_aux_cache.add_missing_ids_query_result["cases_to_ignore"] = cases_to_ignore
                                self.pp_aux_cache.add_missing_ids_query_result["identified_cases"] = identified_cases
                                self.pp_aux_cache.add_missing_ids_query_result["cases_to_choose"] = cases_to_choose
                            with self.el_misc_message_placeholder.container():
                                # display query results in gui
                                for case in identified_cases:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.write(case[0][0][0]["name"])
                                    with col2:
                                        st.write(case[0][2])
                                    with col3:
                                        st.write("-")
                                for index, case in enumerate(cases_to_choose):
                                    description_list = [i["description"] for i in case[0][0]]
                                    description_list.append("-- Select none --")
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.write(case[0][0][0]["name"])
                                    with col2:
                                        selectbox_result.append(
                                            st.selectbox(
                                                label="Select an entity...",
                                                options=description_list,
                                                help="Select the right entity, which should be added to entity library.",
                                                key=f"{index}",
                                            )
                                        )
                                    with col3:
                                        current_selection_index = description_list.index(selectbox_result[index])
                                        if current_selection_index != len(description_list) - 1:
                                            st.write(
                                                f"[Open wikidata entity page](https://www.wikidata.org/wiki/{case[0][0][current_selection_index]['wikidata_id']})"
                                            )
                                        else:
                                            st.write("-")
                                if len(identified_cases) > 0 or len(cases_to_choose) > 0:
                                    # show save button, if new information can be added to entity library
                                    save_add_missing_ids_suggestions_to_loaded_el_button = st.button(
                                        label="Save to currently loaded entity library",
                                        help="Save found and selected IDs to currently loaded entity library. This changes are not saved to the origin file of the entity library. If you want to do so, click 'Save' in entity library submenu after finishing the add missing ids process.",
                                    )
                                    if save_add_missing_ids_suggestions_to_loaded_el_button:
                                        for case in identified_cases:
                                            entity_to_update = self.pp_el_library_object.data[case[1]]
                                            entity_to_update.update(case[0][0][0])
                                        for index, case in enumerate(cases_to_choose):
                                            description_list = [i["description"] for i in case[0][0]]
                                            description_list.append("-- Select none --")
                                            current_selection_index = description_list.index(selectbox_result[index])
                                            if current_selection_index != len(description_list) - 1:
                                                # ignore '-- Select none --' selections
                                                entity_to_update = self.pp_el_library_object.data[case[1]]
                                                entity_to_update.update(case[0][0][current_selection_index])
                                        # reset cache vars and start count-up rerun
                                        self.pp_aux_cache.reset_editor_state()
                                        self.pp_aux_cache.reset_buttons()
                                        self.pp_aux_cache.reset_add_missing_ids_query_result()
                                        self.pp_aux_cache.is_count_up_rerun = True
                                        st.experimental_rerun()
                                else:
                                    st.info("No new data could be retrieved by wikidata query.")
                                    self.pp_aux_cache.reset_add_missing_ids_query_result()

    def if_entity_library_is_loaded_processes(self):
        with self.el_filepath_container:
            if self.pp_el_library_object.data_file is not None:
                self.el_filepath_state_col.latex(state_ok)
                self.el_init_message_placeholder.success("Entity library is activated.")
                editor_init_content = (
                    json.dumps(self.pp_el_library_object.data, indent=4)
                    if self.pp_aux_cache.last_editor_state is None
                    else self.pp_aux_cache.last_editor_state
                )
                if self.pp_aux_cache.is_count_up_rerun == True:
                    self.pp_aux_cache.counter += 1
                    self.pp_aux_cache.reset_is_count_up_rerun()
                with self.el_file_view_placeholder:
                    editor_content = st_ace(
                        value=editor_init_content,
                        height=500,
                        language="json",
                        readonly=False,
                        key=str(self.pp_aux_cache.counter),
                    )
                    editor_content = fix_editor_content(editor_content)
                    logger.info(editor_content)
                if self.pp_aux_cache.last_editor_state is None:
                    self.pp_aux_cache.last_editor_state = editor_content
                if (editor_content) and (editor_content != self.pp_aux_cache.last_editor_state):
                    el_editor_content_check_result = el_editor_content_check(editor_content)
                    if type(el_editor_content_check_result) == str:
                        with self.el_file_view_message_placeholder:
                            with st.container():
                                st.info(f"Error: {el_editor_content_check_result}")
                    else:
                        self.pp_el_library_object.data = json.loads(editor_content)
                        self.pp_aux_cache.last_editor_state = editor_content
                        with self.el_file_view_message_placeholder:
                            with st.container():
                                st.success(
                                    "Currently loaded entity library was successfully updated. To save this changes to file use save or export button."
                                )

    def show(self):
        st.latex("\\text{\Huge{NER Postprocessing}}")
        ## 1. Entity Library
        st.subheader("Entity Library")
        el_container = st.expander(label="Entity Library", expanded=True)
        with el_container:
            # basic layout: filepath subcontainer
            self.filepath_subcontainer()
            # menu control: reset of button states in cache (not button states read from button widgets)
            self.submenu_control()
            # processes triggered by init button
            self.init_button_processes()
            # processes triggered by save button
            self.save_button_processes()
            # processes triggered by export button
            self.export_button_processes()
            # processes triggered by quit button
            self.quit_button_processes()
            # processes triggered by add ids button
            self.add_missing_ids_button_processes()
            # processes triggered if an entity library is loaded (and it has a string value in data_file)
            self.if_entity_library_is_loaded_processes()
            # basic layout and processes: add entities subcontainer and processes
            self.add_entities_from_file_subcontainer_and_processes()

        ## 2. Manual TEI Postprocessing
        tmp.TEIManPP(entity_library=self.pp_el_library_object, aux_cache=self.pp_aux_cache)
