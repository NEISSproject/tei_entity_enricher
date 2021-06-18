import streamlit as st
import logging
import json

from streamlit_ace import st_ace
from typing import Union
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from tei_entity_enricher.interface.postprocessing.io import FileReader, Cache
from tei_entity_enricher.util.exceptions import BadFormat
import tei_entity_enricher.menu.tei_man_postproc as tmp
from tei_entity_enricher.util.helper import state_failed, state_ok, transform_arbitrary_text_to_markdown

logger = logging.getLogger(__name__)


class EntityLibraryLastEditorState:
    """class only used to save the ace editor content of the last run
    to be able to compare the current with the last state"""

    def __init__(self) -> None:
        self.content: str = None

    def set_content(self, content) -> None:
        self.content: str = content

    def reset(self) -> None:
        self.content = None


class EntityLibraryGuiFilepath:
    """class only used to save filepath to cache"""

    def __init__(self) -> None:
        self.filepath: str = None

    def set_filepath(self, path) -> None:
        self.filepath: str = path

    def reset(self) -> None:
        self.filepath = None


@st.cache(allow_output_mutation=True)
def get_entity_library():
    return EntityLibrary(show_printmessages=False)


@st.cache(allow_output_mutation=True)
def get_filepath():
    return EntityLibraryGuiFilepath()


@st.cache(allow_output_mutation=True)
def get_last_editor_state():
    return EntityLibraryLastEditorState()


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


## offenes problem: csv.DictReader kann keine UploadedFiles-Instanzen händeln, obwohl es das laut Dokumentation und Erfahrungsberichten tun sollte
## fehlermeldung:
#   "Error: iterator should return strings, not bytes (did you open the file in text mode?)"
## stand:
#   -code funktioniert mit durch open() bereitgestellten files;
#   -UploadedFiles-klasse bietet read()-mthode an, deren einsatz erzeugt eine andere fehlermeldung:
#       "Error: iterator should return strings, not int (did you open the file in text mode?)"


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
        pp_el_filepath_object: EntityLibraryGuiFilepath = get_filepath()
        pp_el_library_object: EntityLibrary = get_entity_library()
        pp_el_filepath_object.set_filepath(
            pp_el_library_object.default_data_file
        ) if pp_el_filepath_object.filepath is None else None
        pp_el_last_editor_state: EntityLibraryLastEditorState = get_last_editor_state()
        # basic layout: header, entity library container
        st.subheader("Entity Library")
        el_container = st.beta_expander(label="Entity Library", expanded=True)
        with el_container:
            # basic layout: filepath subcontainer
            el_filepath_container = st.beta_container()
            with el_filepath_container:
                el_filepath_field_col, el_filepath_state_col = st.beta_columns([10, 1])
                el_filepath_field = el_filepath_field_col.text_input(
                    label="Filepath",
                    value=pp_el_filepath_object.filepath,
                    help="Enter the filepath to a json file, from which the entity library is loaded.",
                )
                el_create_filepath_if_not_found_checkbox = st.checkbox(
                    label="Create file if not found?",
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
                    label="Export", help="Export the current library state to another filepath (Not yet available)."
                )
                el_add_missing_ids_button = el_add_missing_ids_button_placeholder.button(
                    label="Add missing IDs",
                    help="If an ID is missing in any entity, it will be retrieved on basis of the given information (For the moment: If no id is given at all, no addition atempt is executed due to uncertainess when trying to identify an entity on basis of a name only).",
                )
                el_init_message_placeholder = st.empty()
                el_misc_message_placeholder = st.empty()
                el_file_view_placeholder = st.empty()
                el_file_view_message_placeholder = st.empty()
                # processes triggered by init button
                if el_init_button == True:
                    if pp_el_library_object.data_file is None:
                        pp_el_library_object.data_file = el_filepath_field
                        load_attempt_result = pp_el_library_object.load_library(
                            el_create_filepath_if_not_found_checkbox
                        )
                        if load_attempt_result == True:
                            logger.info(f"Entity library loading process from file {el_filepath_field} succeeded.")
                            pp_el_filepath_object.filepath = el_filepath_field
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
                # processes triggered by export button
                if el_export_button == True:
                    if pp_el_library_object.data_file is not None:
                        pass
                # processes triggered by quit button
                if el_quit_button == True:
                    if pp_el_library_object.data_file is not None:
                        pp_el_library_object.data = None
                        pp_el_library_object.data_file = None
                # processes triggered by add ids button
                if el_add_missing_ids_button == True:
                    if pp_el_library_object.data_file is not None:
                        messages = pp_el_library_object.add_missing_id_numbers()
                        with el_misc_message_placeholder.beta_container():
                            for message in messages:
                                if "changed" in message:
                                    st.success(message)
                                else:
                                    st.info(message)
                # processes triggered if an entity library is loaded (and it has a string value in data_file)
                if pp_el_library_object.data_file is not None:
                    el_filepath_state_col.latex(state_ok)
                    el_init_message_placeholder.success("Entity library is activated.")
                    editor_init_content = (
                        json.dumps(pp_el_library_object.data, indent=4)
                        if pp_el_last_editor_state.content is None
                        else pp_el_last_editor_state.content
                    )
                    with el_file_view_placeholder:
                        editor_content = st_ace(value=editor_init_content, height=500, language="json", readonly=False)
                    if pp_el_last_editor_state.content is None:
                        pp_el_last_editor_state.content = editor_content
                    if (editor_content) and (editor_content != pp_el_last_editor_state.content):
                        el_editor_content_check_result = el_editor_content_check(editor_content)
                        if type(el_editor_content_check_result) == str:
                            with el_file_view_message_placeholder:
                                st.info(f"Error: {el_editor_content_check_result}")
                        else:
                            pp_el_library_object.data = json.loads(editor_content)
                            pp_el_last_editor_state.content = editor_content
                            with el_file_view_message_placeholder:
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
                        # processes triggered by add_entities button
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
                            pp_el_last_editor_state.content = json.dumps(pp_el_library_object.data, indent=4)
                            el_file_view_placeholder.empty()
                            with el_file_view_placeholder:
                                editor_content = st_ace(
                                    value=pp_el_last_editor_state.content,
                                    height=500,
                                    language="json",
                                    readonly=False,
                                )

        ## 2. Manual TEI Postprocessing
        tmp.TEIManPP(self.state, entity_library=pp_el_library_object)
