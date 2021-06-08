import streamlit as st
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_writer_map as tnw_map
import tei_entity_enricher.util.tei_writer as tei_writer


class TEIManPP:
    def __init__(self, state, show_menu=True):
        self.state = state
        if show_menu:
            self.tr = tei_reader.TEIReader(state, show_menu=False)
            self.tnw = tnw_map.TEINERPredWriteMap(state, show_menu=False)
            self.show()

    def tei_edit_environment(self):
        st.write("Loop manually over the predicted tags defined by a TEI NER Prediction Writer Mapping.")
        self.state.tmp_selected_tr_name = st.selectbox(
            "Select a TEI Reader Config!",
            list(self.tr.configdict.keys()),
            index=list(self.tr.configdict.keys()).index(self.state.tmp_selected_tr_name)
            if self.state.tmp_selected_tr_name
            else 0,
            key="tmp_sel_tr",
        )
        selected_tr = self.tr.configdict[self.state.tmp_selected_tr_name]
        self.state.tmp_selected_tnw_name = st.selectbox(
            "Select a TEI Read NER Entity Mapping to test!",
            list(self.tnw.mappingdict.keys()),
            index=list(self.tnw.mappingdict.keys()).index(self.state.tmp_selected_tnw_name)
            if self.state.tmp_selected_tnw_name
            else 0,
            key="tmp_sel_tnw",
        )
        tag_list = tei_writer.build_tag_list_from_tnw(self.tnw.mappingdict[self.state.tmp_selected_tnw_name])
        self.state.tmp_teifile = st.text_input(
           "Choose a TEI File:",
           self.state.tmp_teifile or "",
           key="tnp_tei_file",
        )
        # self.state.tmp_open_teifile = st.file_uploader("Choose a TEI-File", key="tnm_test_file_upload")
        if self.state.tmp_teifile or self.state.tmp_open_teifile:
            tei = tei_writer.TEI_Writer(self.state.tmp_teifile, openfile=self.state.tmp_open_teifile, tr=selected_tr)
            matching_tag_list = tei.get_list_of_tags_matching_tag_list(tag_list)
            self.state.tmp_current_loop_element = st.slider(
                f"Matching tags in the TEI file (found {str(len(matching_tag_list))} entries) ",
                1,
                len(matching_tag_list),
                self.state.tmp_current_loop_element if self.state.tmp_current_loop_element else 0,
                key="tmp_loop_slider",
            )
            st.write(matching_tag_list[self.state.tmp_current_loop_element])

    def show(self):
        st.subheader("Manual TEI Postprocessing")
        man_tei = st.beta_expander("Manual TEI Postprocessing", expanded=True)
        with man_tei:
            self.tei_edit_environment()

# test/0732_101175.xml
