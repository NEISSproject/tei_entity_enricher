import streamlit as st
import logging
import json
import os

from streamlit_ace import st_ace
from typing import Union
from math import floor, trunc
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter, Cache
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

"""
to do:
- Einkapseln mit Sub-Funktionen für bessere Lesbarkeit
"""


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
        used to change ace editor key value between two reruns
    is_rerun : bool
        used to control, if counter is raised in a rerun (ace editor can be changed manually) or not (ace editor can be updated by internal processes)
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

    def set_el_filepath(self, path) -> None:
        self.el_filepath: str = path


@st.cache(allow_output_mutation=True)
def get_entity_library():
    return EntityLibrary(show_printmessages=False)


@st.cache(allow_output_mutation=True)
def get_pp_auxiliary_cache():
    return PostprocessingAuxiliaryCache()


def el_editor_content_check(ace_editor_content: str) -> Union[bool, str]:
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


class TEINERPostprocessing:
    def __init__(self, state, show_menu: bool = True):
        """consists of the entity library control panel and the manual postprocessing panel"""
        if show_menu:
            self.state = state
            self.show()

    def show(self):
        st.latex("\\text{\Huge{NER Postprocessing}}")
        ## 1. Entity Library
        # vars
        pp_el_library_object: EntityLibrary = get_entity_library()
        pp_aux_cache: PostprocessingAuxiliaryCache = get_pp_auxiliary_cache()
        pp_aux_cache.set_el_filepath(
            pp_el_library_object.default_data_file
        ) if pp_aux_cache.el_filepath is None else None
        # basic layout: header, entity library container
        st.subheader("Entity Library")
        el_container = st.beta_expander(label="Entity Library", expanded=True)
        with el_container:
            # basic layout: filepath subcontainer
            el_filepath_container = st.beta_container()
            with el_filepath_container:
                el_filepath_field_col, el_filepath_state_col = st.beta_columns([10, 1])
                el_filepath_field = el_filepath_field_col.text_input(
                    label="Filepath to load from",
                    value=pp_aux_cache.el_filepath,
                    help="Enter the filepath to a json file, from which the entity library is loaded.",
                )
                el_create_filepath_if_not_found_checkbox = st.checkbox(
                    label="Create default file if not found?",
                    value=False,
                    help="If selected, a default library file will be created in the given filepath.",
                )
                (
                    el_col_init_button,
                    el_col_quit_button,
                    el_col_save_button,
                    el_col_export_button,
                    el_col_add_missing_ids_button,
                ) = st.beta_columns(5)
                with el_col_init_button:
                    el_init_button_placeholder = st.empty()
                with el_col_quit_button:
                    el_quit_button_placeholder = st.empty()
                with el_col_save_button:
                    el_save_button_placeholder = st.empty()
                with el_col_export_button:
                    el_export_button_placeholder = st.empty()
                with el_col_add_missing_ids_button:
                    el_add_missing_ids_button_placeholder = st.empty()
                el_init_button = el_init_button_placeholder.button(
                    label="Initialize", key="init", help="Initialize the library from filepath."
                )
                el_quit_button = el_quit_button_placeholder.button(
                    label="Unload", help="Unload the current library (unsaved changes will be lost)."
                )
                el_save_button = el_save_button_placeholder.button(
                    label="Save", help="Save the current library state to filepath."
                )
                el_export_button = el_export_button_placeholder.button(
                    label="Export", help="Export the current library state to another filepath."
                )
                el_add_missing_ids_button = el_add_missing_ids_button_placeholder.button(
                    label="Add missing IDs",
                    help="If an ID is missing in any entity, it will be retrieved on basis of the given information. If no id is given at all, an item of a list of suggestions delivered by wikidata query can be chosen.",
                )
                el_export_filepath_placeholder = st.empty()
                el_add_missing_ids_menu_placeholder = st.empty()
                el_init_message_placeholder = st.empty()
                el_misc_message_placeholder = st.empty()
                el_file_view_placeholder = st.empty()
                el_file_view_message_placeholder = st.empty()
                # menu control: reset of button states in cache (not button states read from button widgets)
                if (
                    el_quit_button == True
                    or el_save_button == True
                    or el_export_button == True
                    or el_add_missing_ids_button == True
                ):
                    pp_aux_cache.reset_buttons()
                # processes triggered by init button
                if el_init_button == True:
                    if pp_el_library_object.data_file is None:
                        pp_el_library_object.data_file = el_filepath_field
                        load_attempt_result = pp_el_library_object.load_library(
                            el_create_filepath_if_not_found_checkbox
                        )
                        if load_attempt_result == True:
                            logger.info(f"Entity library loading process from file {el_filepath_field} succeeded.")
                            pp_aux_cache.el_filepath = el_filepath_field
                        elif type(load_attempt_result) == str:
                            load_attempt_result = transform_arbitrary_text_to_markdown(load_attempt_result)
                            logger.warning(f"Entity library loading process failed: {load_attempt_result}")
                            el_filepath_state_col.latex(state_failed)
                            el_init_message_placeholder.error(load_attempt_result)
                            pp_el_library_object.data_file = None
                # processes triggered by save button
                if el_save_button == True:
                    if pp_el_library_object.data_file is not None:
                        save_attempt_result = pp_el_library_object.save_library()
                        if save_attempt_result == True:
                            el_misc_message_placeholder.success(
                                "The current state of the entity library was successfully saved."
                            )
                        else:
                            el_misc_message_placeholder.error("Could not save current state of entity library.")
                        pp_aux_cache.reset_buttons()
                        pp_aux_cache.reset_add_missing_ids_query_result()
                # processes triggered by export button
                if el_export_button == True or pp_aux_cache.button_export_el == True:
                    if pp_el_library_object.data_file is not None:
                        pp_aux_cache.button_export_el = True
                        el_export_filepath_field_container = el_export_filepath_placeholder.beta_container()
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
                            # el_export_filepath_field_container.button(
                            #     label="Complete export procedure",
                            #     help="Complete export procedure before exporting again.",
                            # )
                            fw = FileWriter(data=pp_el_library_object.data, filepath=el_export_filepath_field)
                            if_file_exists = "replace" if el_export_overwrite_checkbox == True else "cancel"
                            if el_export_create_folder_checkbox == True:
                                makedir_if_necessary(os.path.dirname(el_export_filepath_field))
                            try:
                                fw_return_value = fw.writefile_json(do_if_file_exists=if_file_exists)
                            except FileNotFoundError:
                                fw_return_value = "folder_not_found"
                            if fw_return_value == True:
                                el_misc_message_placeholder.success("Entity Library successfully exported.")
                            elif fw_return_value == False:
                                el_misc_message_placeholder.info("Entity Library export failed: File already exists.")
                            elif fw_return_value == "folder_not_found":
                                el_misc_message_placeholder.info("Entity Library export failed: Folder does not exist.")
                            # pp_aux_cache.reset_buttons()
                # el_export_filepath_placeholder.empty()
                # (((el_export_filepath_placeholder.empty() deletes the export elements,
                # so that the user can not click on exports proceed again,
                # which will cause a rerun without executing an export.
                # at the moment this produces a "Bad message format"-popup)))
                # processes triggered by quit button
                if el_quit_button == True:
                    if pp_el_library_object.data_file is not None:
                        pp_el_library_object.reset()
                        pp_aux_cache.reset_filepath()
                        pp_aux_cache.reset_editor_state()
                        pp_aux_cache.reset_buttons()
                        pp_aux_cache.reset_add_missing_ids_query_result()
                # processes triggered by add ids button
                if el_add_missing_ids_button == True or pp_aux_cache.button_add_missing_ids == True:
                    if pp_el_library_object.data_file is not None:
                        pp_aux_cache.button_add_missing_ids = True
                        with el_add_missing_ids_menu_placeholder.beta_container():
                            progress_bar = st.progress(0)
                            checkbox_state = st.checkbox(
                                label="Try to identify entities without any ids",
                                value=False,
                                help="When activated, for every entity in entity library, which has no id data at all, a list of matching entities will be suggested.",
                            )
                            proceed_button = st.button(
                                label="Query",
                                help="Start process, in which ids will be suggested for the entities in entity library.",
                            )
                            if proceed_button == True or pp_aux_cache.button_add_missing_ids_proceed == True:
                                pp_aux_cache.button_add_missing_ids_proceed = True
                                cases_to_ignore = []
                                identified_cases = []
                                cases_to_choose = []
                                selectbox_result = []
                                if len(pp_aux_cache.add_missing_ids_query_result) > 0:
                                    # load wikidata query results from cache, if they exist
                                    cases_to_ignore = pp_aux_cache.add_missing_ids_query_result["cases_to_ignore"]
                                    identified_cases = pp_aux_cache.add_missing_ids_query_result["identified_cases"]
                                    cases_to_choose = pp_aux_cache.add_missing_ids_query_result["cases_to_choose"]
                                    progress_bar.progress(100)
                                else:
                                    # wikidata query
                                    library_data_length = len(pp_el_library_object.data)
                                    progress_amount = floor((100 / library_data_length) * 10 ** 2) / 10 ** 2
                                    progress_amount_list = list(frange_positve(0, 100, progress_amount))
                                    for index, entity in enumerate(pp_el_library_object.data):
                                        _temp_result_entity_identification = (
                                            pp_el_library_object.return_identification_suggestions_for_entity(
                                                input_entity=entity,
                                                try_to_identify_entities_without_id_values=checkbox_state,
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
                                    pp_aux_cache.add_missing_ids_query_result["cases_to_ignore"] = cases_to_ignore
                                    pp_aux_cache.add_missing_ids_query_result["identified_cases"] = identified_cases
                                    pp_aux_cache.add_missing_ids_query_result["cases_to_choose"] = cases_to_choose
                                with el_misc_message_placeholder.beta_container():
                                    # display query results in gui
                                    for case in identified_cases:
                                        col1, col2, col3 = st.beta_columns(3)
                                        with col1:
                                            st.write(case[0][0][0]["name"])
                                        with col2:
                                            st.write(case[0][2])
                                        with col3:
                                            st.write("-")
                                    for index, case in enumerate(cases_to_choose):
                                        description_list = [i["description"] for i in case[0][0]]
                                        description_list.append("-- Select none --")
                                        col1, col2, col3 = st.beta_columns(3)
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
                                                entity_to_update = pp_el_library_object.data[case[1]]
                                                entity_to_update.update(case[0][0][0])
                                            for index, case in enumerate(cases_to_choose):
                                                description_list = [i["description"] for i in case[0][0]]
                                                description_list.append("-- Select none --")
                                                current_selection_index = description_list.index(
                                                    selectbox_result[index]
                                                )
                                                if current_selection_index != len(description_list) - 1:
                                                    # ignore '-- Select none --' selections
                                                    entity_to_update = pp_el_library_object.data[case[1]]
                                                    entity_to_update.update(case[0][0][current_selection_index])
                                            pp_aux_cache.reset_editor_state()
                                            pp_aux_cache.reset_buttons()
                                            pp_aux_cache.reset_add_missing_ids_query_result()
                                            pp_aux_cache.is_count_up_rerun = True
                                            st.experimental_rerun()
                                            # with el_misc_message_placeholder:
                                            #     st.success("Found and selected suggestions successfull saved to entity library.")
                                            # st.button(label="Close add-missing-ids submenus")
                                            # update ace-editor-content (empty placeholder and create new instance)
                                            # el_file_view_placeholder.empty()
                                            # with el_file_view_placeholder:
                                            #     editor_content = st_ace(
                                            #         value=pp_aux_cache.last_editor_state,
                                            #         height=500,
                                            #         language="json",
                                            #         readonly=False,
                                            #         key="third",
                                            #     )
                                            # with el_file_view_message_placeholder:
                                            #     with st.beta_container():
                                            #         st.button(
                                            #             label="Rerun first before manually edit the entity library again",
                                            #             help="At the moment the postprocessing page has to be reloaded after a change of the current entity library.",
                                            #         )
                                    else:
                                        st.info("No new data could be retrieved by wikidata query.")
                                        pp_aux_cache.reset_add_missing_ids_query_result()

                # processes triggered if an entity library is loaded (and it has a string value in data_file)
                if pp_el_library_object.data_file is not None:
                    el_filepath_state_col.latex(state_ok)
                    el_init_message_placeholder.success("Entity library is activated.")
                    editor_init_content = (
                        json.dumps(pp_el_library_object.data, indent=4)
                        if pp_aux_cache.last_editor_state is None
                        else pp_aux_cache.last_editor_state
                    )
                    if pp_aux_cache.is_count_up_rerun == True:
                        pp_aux_cache.counter += 1
                        pp_aux_cache.is_count_up_rerun = False
                    with el_file_view_placeholder:
                        editor_content = st_ace(
                            value=editor_init_content,
                            height=500,
                            language="json",
                            readonly=False,
                            key=str(pp_aux_cache.counter),
                        )
                        logger.info(editor_content)
                    if pp_aux_cache.last_editor_state is None:
                        pp_aux_cache.last_editor_state = editor_content
                    if (editor_content) and (editor_content != pp_aux_cache.last_editor_state):
                        el_editor_content_check_result = el_editor_content_check(editor_content)
                        if type(el_editor_content_check_result) == str:
                            with el_file_view_message_placeholder:
                                with st.beta_container():
                                    st.info(f"Error: {el_editor_content_check_result}")
                                    # st.button(
                                    #     label="Rerun first before manually edit the entity library again",
                                    #     help="At the moment the postprocessing page has to be reloaded after a manual change of the current entity library, before a manual change can be executed again.",
                                    # )
                        else:
                            pp_el_library_object.data = json.loads(editor_content)
                            pp_aux_cache.last_editor_state = editor_content
                            with el_file_view_message_placeholder:
                                with st.beta_container():
                                    st.success(
                                        "Currently loaded entity library was successfully updated. To save this changes to file use save or export button."
                                    )
            # basic layout: add entities subcontainer
            el_add_entities_from_file_subcontainer = st.beta_container()
            with el_add_entities_from_file_subcontainer:
                el_add_entities_from_file_loader_placeholder = st.empty()
                el_add_entities_from_file_button_placeholder = st.empty()
                el_add_entities_from_file_success_message_placeholder = st.empty()
                # processes triggered if an entity library is loaded (and it has a string value in data_file)
                if pp_el_library_object.data_file is not None:
                    el_add_entities_from_file_loader_file_list = el_add_entities_from_file_loader_placeholder.file_uploader(
                        label="Add entities from file",
                        type=["json", "csv"],
                        accept_multiple_files=True,
                        key=None,
                        help="Use json or csv files to add entities to the loaded library. Importing multiple files at once is possible, see the documentation for file structure requirements.",
                    )
                    if len(el_add_entities_from_file_loader_file_list) > 0:
                        el_add_entities_from_file_button_value = el_add_entities_from_file_button_placeholder.button(
                            label="Start adding process", key=None, help=None
                        )
                        # processes triggered by add entities button
                        if el_add_entities_from_file_button_value == True:
                            result_messages = []
                            for uploaded_file in el_add_entities_from_file_loader_file_list:
                                el_add_entities_from_file_single_file_result = (
                                    pp_el_library_object.add_entities_from_file(file=uploaded_file)
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
                                with el_add_entities_from_file_success_message_placeholder.beta_container():
                                    for message in result_messages:
                                        if "success" in message:
                                            st.success(message)
                                        else:
                                            st.info(message)
                            pp_aux_cache.last_editor_state = json.dumps(pp_el_library_object.data, indent=4)
                            pp_aux_cache.is_count_up_rerun = True
                            # st.experimental_rerun()
                            st.button(label="Finish process")

        ## 2. Manual TEI Postprocessing
        tmp.TEIManPP(self.state, entity_library=pp_el_library_object, aux_cache=pp_aux_cache)
