import streamlit as st
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_writer_map as tnw_map
import tei_entity_enricher.menu.tei_ner_map as tnm_map
import tei_entity_enricher.util.tei_writer as tei_writer
from tei_entity_enricher.util.components import editable_multi_column_table
from tei_entity_enricher.util.helper import transform_arbitrary_text_to_markdown, transform_xml_to_markdown
#from tei_entity_enricher.interface.postprocessing.identifier import Identifier

class TEIManPP:
    def __init__(self, state, show_menu=True):
        self.state = state
        self.search_options=['By TEI NER Prediction Writer Mapping','By TEI Read NER Entity Mapping','By self-defined Tag configuration']
        if show_menu:
            self.tr = tei_reader.TEIReader(state, show_menu=False)
            self.tnm = tnm_map.TEINERMap(state, show_menu=False)
            self.tnw = tnw_map.TEINERPredWriteMap(state, show_menu=False)
            self.show()

    def show_editable_attr_value_def(self, tagname, tagbegin):
        st.markdown("Editable Attributes and Values for current search result!")
        entry_dict = {"Attributes": [], "Values": []}
        if tagbegin.endswith("/>"):
            end=-2
        else:
            end=-1
        attr_list=tagbegin[len(tagname)+2:end].split(" ")
        for element in attr_list:
            if "=" in element:
                attr_value=element.split("=")
                entry_dict["Attributes"].append(attr_value[0])
                entry_dict["Values"].append(attr_value[1][1:-1])
        answer = editable_multi_column_table(entry_dict, None, openentrys=20)
        new_tagbegin="<"+tagname
        attrdict={}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in attrdict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            attrdict[answer["Attributes"][i]] = answer["Values"][i]
            new_tagbegin=new_tagbegin+" "+answer["Attributes"][i]+'="'+answer["Values"][i]+'"'
        new_tagbegin=new_tagbegin+">"
        return new_tagbegin

    def show_sd_search_attr_value_def(self, attr_value_dict, name):
        st.markdown("Define optionally attributes with values which have to be mandatory for the search!")
        entry_dict = {"Attributes": [], "Values": []}
        for key in attr_value_dict.keys():
            entry_dict["Attributes"].append(key)
            entry_dict["Values"].append(attr_value_dict[key])
        answer = editable_multi_column_table(entry_dict, "tnw_attr_value" + name, openentrys=20)
        returndict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in returndict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            returndict[answer["Attributes"][i]] = answer["Values"][i]
        return returndict


    def tei_edit_specific_entity(self,tag_entry):
        col1, col2 = st.beta_columns(2)
        with col1:
            tag_entry['name']=st.text_input("Editable Tag Name",tag_entry['name'],key='tmp_edit_ent_name',help="Here you can change the name of the tag.")
            tag_entry['tagbegin'] = self.show_editable_attr_value_def(tag_entry['name'],tag_entry['tagbegin'])
        with col2:
            st.markdown("### Textcontent of the tag:")
            if "pure_tagcontent" in tag_entry.keys():
                st.markdown(transform_arbitrary_text_to_markdown(tag_entry["pure_tagcontent"]))
            st.markdown("### Full tag in xml:")
            st.markdown(transform_xml_to_markdown(tei_writer.get_full_xml_of_tree_content(tag_entry)))
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
                self.state.tmp_matching_tag_list = tei.get_list_of_tags_matching_tag_list(tag_list)
                self.state.tmp_current_loop_element=1
                if len(self.state.tmp_matching_tag_list)>0:
                    self.enrich_search_list_with_pure_tagcontent(selected_tr)
                    if self.state.pp_el_object:
                        self.enrich_search_list_with_link_suggestions()
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
            else:
                self.state.tmp_sd_search_tag = st.text_input(
                        "Define a Tag as search criterion",
                        self.state.tmp_sd_search_tag or "",
                        key="tmp_sd_search_tag",help="Define a Tag as a search criterion!"
                    )
                self.state.tmp_sd_search_tag_attr_dict = self.show_sd_search_attr_value_def(self.state.tmp_sd_search_tag_attr_dict if self.state.tmp_sd_search_tag_attr_dict else {}, "tmp_sd_search_tag_attr_dict")
                tag_list=[[self.state.tmp_sd_search_tag,self.state.tmp_sd_search_tag_attr_dict]]
        return tag_list

    def enrich_search_list_with_pure_tagcontent(self,tr):
        for tag in self.state.tmp_matching_tag_list:
            if "tagcontent" in tag.keys():
                tag["pure_tagcontent"]=tei_writer.get_pure_text_of_tree_element(tag["tagcontent"],tr)


    def enrich_search_list_with_link_suggestions(self):
        entitylist=[]
        #for tag in self.state.tmp_matching_tag_list:
        #    entitylist.append(tuple())
        #Identifier()


    def show(self):
        st.subheader("Manual TEI Postprocessing")
        man_tei = st.beta_expander("Manual TEI Postprocessing", expanded=True)
        with man_tei:
            self.tei_edit_environment()

# test/0732_101175.xml
