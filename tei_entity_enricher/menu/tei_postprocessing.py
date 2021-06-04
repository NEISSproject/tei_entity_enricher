import streamlit as st
from tei_entity_enricher.interface.postprocessing.entity_library import EntityLibrary
from tei_entity_enricher.interface.postprocessing.io import FileReader
import tei_entity_enricher.menu.tei_man_postproc as tmp


class TEINERPostprocessing:
    def __init__(self, state, show_menu: bool = True):
        self.state = state
        if show_menu:
            self.show()

    def get_el_filepath(self):
        saved_filepath = None
        # todo: check in state (?) if a custom filepath has been choosen to load the entity library from
        if saved_filepath is None:
            entity_library = EntityLibrary()
            return entity_library.data_file

    def show(self):
        st.latex("\\text{\Huge{NER Postprocessing}}")
        entity_library_container = st.beta_container()
        identifier_container = st.beta_container()

        with entity_library_container:
            st.subheader("Entity Library")
            with st.form("entity library file"):
                el_filepath = st.text_input(
                    "Filepath",
                    value=self.get_el_filepath(),
                    help="filepath to entity_library.json, from which the entity library is loaded",
                )
                submit_button = st.form_submit_button(label="Initialize Library from filepath")
                if submit_button:
                    if el_filepath:
                        el_file_preview = st.json(FileReader(el_filepath, "local", True, True).loadfile_json())
                        st.success("Entity Library has been initialized")
            with st.beta_expander("Add entities from file"):
                el_add_from_file = st.file_uploader(
                    "",
                    ["json", "csv"],
                    False,
                    None,
                    "use json or csv files to add entities to the library",
                )
                if el_add_from_file is not None:
                    st.write("File successfully loaded...")

        # col1, col2 = st.beta_columns(2)
        # with col1:
        #     self.show_configs()
        # with col2:
        #     self.show_edit_environment()
        # self.show_test_environment()
        tmp.TEIManPP(self.state)
