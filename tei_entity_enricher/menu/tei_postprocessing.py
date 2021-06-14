import streamlit as st
import logging
from streamlit_ace import st_ace
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
import tei_entity_enricher.menu.tei_man_postproc as tmp
from tei_entity_enricher.util.helper import state_failed, state_ok, transform_arbitrary_text_to_markdown

logger = logging.getLogger(__name__)


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


## offenes problem: csv.DictReader kann keine UploadedFiles-Instanzen händeln, obwohl es das laut Dokumentation und Erfahrungsberichten tun sollte
## fehlermeldung:
#   "Error: iterator should return strings, not bytes (did you open the file in text mode?)"
## stand:
#   -code funktioniert mit durch open() bereitgestellten files;
#   -UploadedFiles-klasse bietet read()-mthode an, deren einsatz erzeugt eine andere fehlermeldung:
#       "Error: iterator should return strings, not int (did you open the file in text mode?)"


class TEINERPostprocessing:
    def __init__(self, show_menu: bool = True):
        """consists of the entity library control panel and the manual postprocessing panel"""
        if show_menu:
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
        # basic layout: header, entity library container and filepath container
        st.subheader("Entity Library")
        el_container = st.beta_expander(label="Entity Library", expanded=True)
        with el_container:
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
                el_col_init_button, el_col_quit_button, el_col_save_button, el_col_export_button = st.beta_columns(4)
                # hier wieder bedingungen einfügen (yeah!) warum kann man deklarierte buttons nicht wieder leeren? vielleicht einen empty()-container jeweils als placeholder in die columns platzieren und die dann ansteuern?
                el_init_button = el_col_init_button.button(
                    label="Initialize", help="Initialize the library from filepath."
                )
                el_quit_button = st.empty()
                el_save_button = None
                el_export_button = None
                el_file_editor = st.empty()
                el_init_message = st.empty()
                el_misc_message = st.empty()
                # processes triggered by init button
                if el_init_button == True:
                    pp_el_library_object.data_file = el_filepath_field
                    load_attempt_result = pp_el_library_object.load_library(el_create_filepath_if_not_found_checkbox)
                    if load_attempt_result == True:
                        logger.info(f"Entity library loading process from file {el_filepath_field} succeeded.")
                        pp_el_filepath_object.filepath = el_filepath_field
                    elif type(load_attempt_result) == str:
                        load_attempt_result = transform_arbitrary_text_to_markdown(load_attempt_result)
                        logger.warning(f"Entity library loading process failed: {load_attempt_result}")
                        el_filepath_state_col.latex(state_failed)
                        el_init_message.error(load_attempt_result)
                        pp_el_library_object.data_file = None
                # processes triggered by save button
                if el_save_button == True:
                    save_attempt_result = pp_el_library_object.save_library()
                    if save_attempt_result == True:
                        el_misc_message.success("The current state of the entity library was successfully saved.")
                    else:
                        el_misc_message.error("Could not save current state of entity library.")
                # processes triggered by export button
                if el_export_button == True:
                    pass
                # processes triggered by quit button
                if el_quit_button == True:
                    el_misc_message.empty()
                    el_init_message.empty()
                    pp_el_library_object.data = None
                    pp_el_library_object.data_file = None
                # processes triggered if an entity library is loaded (and it has a string value in data_file)
                if pp_el_library_object.data_file is not None:
                    el_col_init_button = None
                    el_quit_button = el_col_quit_button.button(
                        label="Unload", help="Unload the current library (unsaved changes will be lost)."
                    )
                    el_save_button = el_col_save_button.button(
                        label="Save", help="Save the current library state to filepath."
                    )
                    el_export_button = el_col_export_button.button(
                        label="Export", help="Export the current library state to another filepath (Not yet available)."
                    )
                    el_filepath_state_col.latex(state_ok)
                    # el_file_editor = st_ace(value=pp_el_library_object.data, height=500, language=None, readonly=True)
                    el_file_editor = st.json(pp_el_library_object.data)
                    el_init_message = st.success("Entity library is activated.")
            # basic layoout: add entities widget
            el_add_entities_from_file_subcontainer = st.beta_container()
            with el_add_entities_from_file_subcontainer:
                el_add_entities_from_file_loader = st.empty()
                el_add_entities_from_file_button = st.empty()
                el_add_entities_from_file_button_value = None
                el_add_entities_from_file_success_message = st.empty()
                # processes triggered if an entity library is loaded (and it has a string value in data_file)
                if pp_el_library_object.data_file is not None:
                    el_add_entities_from_file_loader_file_list = el_add_entities_from_file_loader.file_uploader(
                        label="Add entities from file",
                        type=["json", "csv"],
                        accept_multiple_files=True,
                        key=None,
                        help="Use json or csv files to add entities to the loaded library. Importing multiple files at once is possible, see the documentation for file structure requirements.",
                    )
                    if len(el_add_entities_from_file_loader_file_list) > 0:
                        el_add_entities_from_file_button_value = el_add_entities_from_file_button.button(
                            label="Start adding process", key=None, help=None
                        )
                    # processes triggered by add_entities button
                    if el_add_entities_from_file_button_value == True:
                        result_messages = []
                        for uploaded_file in el_add_entities_from_file_loader_file_list:
                            el_add_entities_from_file_single_file_result = pp_el_library_object.add_entities_from_file(
                                file=uploaded_file
                            )
                            logger.info(
                                f"add_entities_from_file() result: {el_add_entities_from_file_single_file_result}. is el_add_entities_from_file_single_file_result[0] == 0?: {el_add_entities_from_file_single_file_result[0] == 0}"
                            )
                            if type(el_add_entities_from_file_single_file_result) == str:
                                result_messages.append(el_add_entities_from_file_single_file_result)
                            else:
                                result_messages.append(
                                    f"{el_add_entities_from_file_single_file_result[0]} entity/ies was/were successfully added to entity library. But {el_add_entities_from_file_single_file_result[1]} entity/ies was/were ignored due to redundance issues."
                                )
                            with el_add_entities_from_file_success_message.beta_container():
                                for message in result_messages:
                                    if "success" in message:
                                        st.success(message)
                                    else:
                                        st.info(message)

        ## 2. Manual TEI Postprocessing
        # tmp.TEIManPP(self.state)
