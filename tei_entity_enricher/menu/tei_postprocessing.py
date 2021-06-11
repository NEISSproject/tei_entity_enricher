import streamlit as st
import logging
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
import tei_entity_enricher.menu.tei_man_postproc as tmp
from tei_entity_enricher.util.helper import state_failed, state_ok, transform_arbitrary_text_to_markdown

logger = logging.getLogger(__name__)


## offenes problem: csv.DictReader kann keine UploadedFiles-Instanzen händeln, obwohl es das laut Dokumentation und Erfahrungsberichten tun sollte
## fehlermeldung:
#   "Error: iterator should return strings, not bytes (did you open the file in text mode?)"
## stand:
#   -code funktioniert mit durch open() bereitgestellten files;
#   -UploadedFiles-klasse bietet read()-mthode an, deren einsatz erzeugt eine andere fehlermeldung:
#       "Error: iterator should return strings, not int (did you open the file in text mode?)"


class TEINERPostprocessing:
    def __init__(self, state, show_menu: bool = True):
        """consists of the entity library control panel and the manual postprocessing panel

        used state variables:
        ---------------------
        pp_el_filepath: str
        pp_el_object: list with dicts (from json)
        pp_el_upload_messages: list with strings
        pp_el_reload_counter: int"""
        self.state = state
        if show_menu:
            self.show()

    def init_el_state_variables(self):
        """initialize state variables:
        pp_el_filepath = default path defined in EntityLibrary class
        pp_el_object is not initialized because its init value, when queried from state, is already None
        pp_el_upload_messages is not initialized because it is used (defined and emptied) just locally in add entities process
        pp_el_reload_counter is not initialized because it is used (defined and emptied) just locally in add entities process"""
        if self.state.pp_el_filepath is None:
            entity_library = EntityLibrary(show_printmessages=False)
            self.state.pp_el_filepath = entity_library.data_file

    def reset_el_state_variable(self, variable: str):
        """reset one or all state variables to init state"""

        def fp():
            default_fp = EntityLibrary(show_printmessages=False).data_file
            self.state.pp_el_filepath = default_fp

        def object():
            self.state.pp_el_object = None

        def upload_messages():
            self.state.pp_el_upload_messages = None

        def reload_counter():
            self.state.pp_el_reload_counter = None

        def all():
            fp()
            object()
            upload_messages()
            reload_counter()

        def fallback():
            return None

        call_dict = {
            "pp_el_filepath": fp,
            "pp_el_object": object,
            "pp_el_upload_messages": upload_messages,
            "pp_el_reload_counter": reload_counter,
            "all": all,
        }
        call_dict.get(variable, fallback)()

    def show(self):
        st.latex("\\text{\Huge{NER Postprocessing}}")
        ## 1. Entity Library
        # vars
        self.init_el_state_variables()
        # layout (including state.pp_el_object value dependency)
        st.subheader("Entity Library")
        el_container = st.beta_expander(label="Entity Library", expanded=True)
        with el_container:
            el_filepath_container = st.beta_container()
            with el_filepath_container:
                el_filepath_field_col, el_filepath_state_col = st.beta_columns([10, 1])
                el_filepath_field = el_filepath_field_col.text_input(
                    label="Filepath",
                    value=self.state.pp_el_filepath,
                    help="Enter the filepath to a json file, from which the entity library is loaded.",
                )
                el_create_filepath_if_not_found_checkbox = st.checkbox(
                    label="Create file if not found?",
                    value=False,
                    help="If selected, a default library file will be created in the given filepath.",
                )
                el_col_init_button, el_col_quit_button, el_col_save_button, el_col_export_button = st.beta_columns(4)
                if self.state.pp_el_object is None:
                    el_init_button = el_col_init_button.button(
                        label="Initialize", help="Initialize the library from filepath."
                    )
                    el_quit_button = None
                    el_save_button = None
                    el_export_button = None
                else:
                    el_init_button = True
                    el_quit_button = el_col_quit_button.button(
                        label="Unload", help="Unload the current library (unsaved changes will be lost)."
                    )
                    el_save_button = el_col_save_button.button(
                        label="Save", help="Save the current library state to filepath."
                    )
                    el_export_button = el_col_export_button.button(
                        label="Export", help="Export the current library state to another filepath (Not yet available)."
                    )
                el_init_message = st.empty()
                el_misc_message = st.empty()
                el_file_preview = st.empty()
            el_add_entities_from_file_subcontainer = st.beta_container()
            with el_add_entities_from_file_subcontainer:
                if self.state.pp_el_object is None:
                    el_add_entities_from_file_loader = None
                    el_add_entities_from_file_button = st.empty()
                else:
                    el_add_entities_from_file_loader = st.file_uploader(
                        label="Add entities from file",
                        type=["json", "csv"],
                        accept_multiple_files=True,
                        key=None,
                        help="Use json or csv files to add entities to the loaded library. Importing multiple files at once is possible, see the documentation for file structure requirements.",
                    )
                    if len(el_add_entities_from_file_loader) > 0:
                        el_add_entities_from_file_button = st.button(label="Start adding process", key=None, help=None)
                    else:
                        el_add_entities_from_file_button = st.empty()
                el_add_entities_from_file_success_message = st.empty()
        # processes
        if el_init_button == True:
            if self.state.pp_el_object is None:
                el_instance = EntityLibrary(data_file=None, show_printmessages=False)
                el_instance.data_file = el_filepath_field
                load_attempt_result = el_instance.load_library(el_create_filepath_if_not_found_checkbox)
                if load_attempt_result == True:
                    logger.info(f"Entity library loading process from file {el_filepath_field} succeeded.")
                    el_filepath_state_col.latex(state_ok)
                    self.state.pp_el_object = el_instance
                    self.state.pp_el_filepath = el_instance.data_file
                    el_file_preview.json(self.state.pp_el_object.data)
                    el_init_message.success("Entity library is activated.")
                elif type(load_attempt_result) == str:
                    load_attempt_result = transform_arbitrary_text_to_markdown(load_attempt_result)
                    logger.warning(f"Entity library loading process failed: {load_attempt_result}")
                    el_filepath_state_col.latex(state_failed)
                    el_init_message.error(load_attempt_result)
            else:
                el_filepath_state_col.latex(state_ok)
                el_file_preview.json(self.state.pp_el_object.data)
                el_init_message.success("Entity library is activated.")
        if el_save_button == True:
            save_attempt_result = self.state.pp_el_object.save_library()
            if save_attempt_result == True:
                el_misc_message.success("The current state of the entity library was successfully saved.")
            else:
                el_misc_message.error("Could not save current state of entity library.")
        if el_export_button == True:
            pass
        if el_quit_button == True:
            el_misc_message.empty()
            el_init_message.empty()
            self.reset_el_state_variable("pp_el_object")
        if el_add_entities_from_file_button == True:
            self.state.pp_el_upload_messages = []
            for uploaded_file in el_add_entities_from_file_loader:
                el_add_entities_from_file_single_file_result = self.state.pp_el_object.add_entities_from_file(
                    file=uploaded_file
                )
                logger.info(
                    f"add_entities_from_file() result: {el_add_entities_from_file_single_file_result}. is el_add_entities_from_file_single_file_result[0] == 0?: {el_add_entities_from_file_single_file_result[0] == 0}"
                )
                if el_add_entities_from_file_single_file_result[0] == 0:
                    self.state.pp_el_upload_messages.append(
                        f"Data from {uploaded_file.name} successfully added to library. {el_add_entities_from_file_single_file_result[1]} entity/ies has/have been ignored due to redundance issues."
                    )
                if type(el_add_entities_from_file_single_file_result) == str:
                    self.state.pp_el_upload_messages.append(
                        f"Data from {uploaded_file.name} not added to library: {el_add_entities_from_file_single_file_result}"
                    )
            logger.info(self.state.pp_el_upload_messages)
            self.state.pp_el_reload_counter = 2
        if self.state.pp_el_upload_messages is not None:
            with el_add_entities_from_file_success_message.beta_container():
                for message in self.state.pp_el_upload_messages:
                    if "successfully" in message:
                        st.success(message)
                    else:
                        st.info(message)
            if self.state.pp_el_reload_counter == 0:
                self.reset_el_state_variable("pp_el_upload_messages")
                self.state.pp_el_reload_counter = None
            else:
                self.state.pp_el_reload_counter = self.state.pp_el_reload_counter - 1
        ## 2. Manual TEI Postprocessing
        tmp.TEIManPP(self.state)
