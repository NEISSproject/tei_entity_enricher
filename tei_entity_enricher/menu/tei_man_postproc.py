import streamlit as st
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_writer_map as tnw_map
import tei_entity_enricher.menu.tei_ner_map as tnm_map
import tei_entity_enricher.util.tei_writer as tei_writer
from tei_entity_enricher.util.components import editable_multi_column_table
from tei_entity_enricher.util.helper import transform_arbitrary_text_to_markdown

def extract_attributes_and_values(tag,tagbegin):
    attr_dict={}
    attr_list=tagbegin[len(tag)+2:-1].split(" ")
    for element in attr_list:
        attr_value=element.split("=")
        attr_dict[attr_value[0]]=attr_value[1][1:-1]
    return attr_dict

class TEIManPP:
    def __init__(self, state, show_menu=True):
        self.state = state
        self.search_options=['By TEI NER Prediction Writer Mapping','By TEI Read NER Entity Mapping','By self-defined Tag configuration']
        if show_menu:
            self.tr = tei_reader.TEIReader(state, show_menu=False)
            self.tnm = tnm_map.TEINERMap(state, show_menu=False)
            self.tnw = tnw_map.TEINERPredWriteMap(state, show_menu=False)
            self.show()

    def show_editable_attr_value_def(self, tagname, tagbegin, name):
        st.markdown("Editable Attributes and Values for current search result!")
        entry_dict = {"Attributes": [], "Values": []}
        attr_list=tagbegin[len(tagname)+2:-1].split(" ")
        for element in attr_list:
            attr_value=element.split("=")
            entry_dict["Attributes"].append(attr_value[0])
            entry_dict["Values"].append(attr_value[1][1:-1])
        answer = editable_multi_column_table(entry_dict, name, openentrys=20)
        new_tagbegin="<"+tagname
        attrdict={}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in attrdict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            attrdict[answer["Attributes"][i]] = answer["Values"][i]
            new_tagbegin=new_tagbegin+" "+answer["Attributes"][i]+'="'+answer["Values"][i]+'"'
        new_tagbegin=new_tagbegin+">"
        return new_tagbegin


    def tei_edit_specific_entity(self,tag_entry):
        col1, col2 = st.beta_columns(2)
        with col1:
            tag_entry['name']=st.text_input("Editable Tag Name",tag_entry['name'],key='tmp_edit_ent_name',help="Here you can change the name of the tag.")
            tag_entry['tagbegin'] = self.show_editable_attr_value_def(tag_entry['name'],tag_entry['tagbegin'],'tmp_edit_search_attr_dict')
        with col2:
            st.markdown("### Textcontent of the tag:")
            st.markdown(transform_arbitrary_text_to_markdown(tei_writer.get_pure_text_of_tree_element(tag_entry["tagcontent"],self.state.tmp_cur_tr)))
            st.markdown("### Full tag in xml:")
            st.markdown(transform_arbitrary_text_to_markdown(tei_writer.get_full_xml_of_tree_content(tag_entry)))
        return tag_entry

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
        tag_list = self.define_search_criterion()
        self.state.tmp_teifile = st.text_input(
           "Choose a TEI File:",
           self.state.tmp_teifile or "",
           key="tnp_tei_file",
        )
        # self.state.tmp_open_teifile = st.file_uploader("Choose a TEI-File", key="tnm_test_file_upload")
        #if self.state.tmp_teifile or self.state.tmp_open_teifile:
        if st.button('Search Matching Entities in TEI-File:'):
            if self.state.tmp_teifile or self.state.tmp_open_teifile:
                tei = tei_writer.TEI_Writer(self.state.tmp_teifile, openfile=self.state.tmp_open_teifile, tr=selected_tr)
                self.state.tmp_cur_tr=selected_tr
                self.state.tmp_matching_tag_list = tei.get_list_of_tags_matching_tag_list(tag_list)
                self.state.tmp_current_loop_element=1
            else:
                self.state.avoid_rerun()
                self.state.tmp_matching_tag_list = []
                st.warning("Please select a TEI file to be searched for entities.")

        if self.state.tmp_matching_tag_list is None:
            st.info("Use the search button to loop through a TEI file for the entities specified above.")
        elif len(self.state.tmp_matching_tag_list)<1:
            st.warning("The last search resulted in no matching entities.")
        else:
            self.state.tmp_current_loop_element = st.slider(
                f"Matching tags in the TEI file (found {str(len(self.state.tmp_matching_tag_list))} entries) ",
                1,
                len(self.state.tmp_matching_tag_list),
                self.state.tmp_current_loop_element if self.state.tmp_current_loop_element else 1,
                key="tmp_loop_slider",
            )
            self.state.tmp_current_loop_element=st.number_input("Goto Search Result with Index:",1,len(self.state.tmp_matching_tag_list),self.state.tmp_current_loop_element)
            self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element-1]=self.tei_edit_specific_entity(self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element-1])
            st.write(self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element-1])

    def define_search_criterion(self):
        col1, col2 = st.beta_columns(2)
        with col1:
            self.state.tmp_search_options = st.radio(
                "Shuffle Options",
                self.search_options,
                self.search_options.index(self.state.tmp_search_options)
                if self.state.tmp_search_options
                else 0,
            )
        with col2:
            if self.search_options.index(self.state.tmp_search_options)==0:
                self.state.tmp_selected_tnw_name = st.selectbox(
                    "Select a TEI NER Prediction Writer Mapping as search criterion!",
                    list(self.tnw.mappingdict.keys()),
                    index=list(self.tnw.mappingdict.keys()).index(self.state.tmp_selected_tnw_name)
                    if self.state.tmp_selected_tnw_name
                    else 0,
                    key="tmp_sel_tnw",
                )
                tag_list = tei_writer.build_tag_list_from_entity_dict(self.tnw.mappingdict[self.state.tmp_selected_tnw_name]["entity_dict"],"tnw")
            elif self.search_options.index(self.state.tmp_search_options)==1:
                self.state.tmp_selected_tnm_name = st.selectbox(
                    "Select a TEI Read NER Entity Mapping as search criterion!",
                    list(self.tnm.mappingdict.keys()),
                    index=list(self.tnm.mappingdict.keys()).index(self.state.tmp_selected_tnm_name)
                    if self.state.tmp_selected_tnm_name
                    else 0,
                    key="tmp_sel_tnm",
                )
                tag_list = tei_writer.build_tag_list_from_entity_dict(self.tnm.mappingdict[self.state.tmp_selected_tnm_name]["entity_dict"],"tnm")
        return tag_list

    def show(self):
        st.subheader("Manual TEI Postprocessing")
        man_tei = st.beta_expander("Manual TEI Postprocessing", expanded=True)
        with man_tei:
            self.tei_edit_environment()

# test/0732_101175.xml
