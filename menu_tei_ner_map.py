import streamlit as st
import TEIEntityEnricher.tei_parser as tp
import json
import os
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

class Menu_ner_tei_map():
    def __init__(self,state):
        self.state=state

        #self.config_Folder='TR_Configs'
        #self.template_config_Folder=os.path.join('TEIEntityEnricher','Templates',self.config_Folder)
        #self.tr_config_attr_name='name'
        #self.tr_config_attr_excl_tags='exclude_tags'
        #self.tr_config_attr_use_notes='use_notes'
        #self.tr_config_attr_note_tags='note_tags'
        #self.tr_config_attr_template='template'
        self.tnm_config_mode_add='add'
        self.tnm_config_mode_dupl='duplicate'
        self.tnm_config_mode_edit='edit'

        self.show()



    def teinermapadd(self):
        pass
        #self.show_editable_config_content(self.tr_config_mode_add)

    def teinermapdupl(self):
        pass
        #self.show_editable_config_content(self.tr_config_mode_dupl)

    def teinermapedit(self):
        pass
        #self.show_editable_config_content(self.tr_config_mode_edit)

    def teinermapdel(self):
        pass
        #selected_config_name=st.selectbox('Select a TEI NER Map to delete!',self.editable_config_names)
        #if st.button('Delete Selected Config'):
        #    self.validate_and_delete_config(self.configdict[selected_config_name])

    def show_edit_environment(self):
        tr_config_definer = st.beta_expander("Add or edit existing TEI NER Entity Mapping", expanded=False)
        with tr_config_definer:
            options = {
                "Add TEI NER Entity Mapping": self.teinermapadd,
                "Duplicate TEI NER Entity Mapping": self.teinermapdupl,
                "Edit TEI NER Entity Mapping": self.teinermapedit,
                "Delete TEI NER Entity Mapping": self.teinermapdel
                }
            self.state.tnm_edit_options = st.radio("Edit Options", tuple(options.keys()),tuple(options.keys()).index(self.state.tnm_edit_options) if self.state.tnm_edit_options else 0)
            options[self.state.tnm_edit_options]()


    def show_test_environment(self):
        tr_test_expander = st.beta_expander("Test TEI NER Entity Mapping", expanded=False)


    def build_config_tablestring(self):
        tablestring='Name | Exclude Tags | Tagging Notes | Note Tags | Template \n -----|-------|-------|-------|-------'
        for config in self.configslist:
            if config[self.tr_config_attr_use_notes]:
                use_notes='yes'
            else:
                use_notes='no'
            if config[self.tr_config_attr_template]:
                template='yes'
            else:
                template='no'
            tablestring+='\n ' + config[self.tr_config_attr_name] + ' | ' + self.get_listoutput(config[self.tr_config_attr_excl_tags]) +  ' | ' + use_notes + ' | ' + self.get_listoutput(config[self.tr_config_attr_note_tags]) +  ' | ' + template
        return tablestring


    def show_configs(self):
        tr_show_configs = st.beta_expander("Existing TEI NER Entity Mappings", expanded=True)



    def show(self):
        st.latex('\\text{\Huge{TEI NER Entity Mapping}}')
        col1, col2 = st.beta_columns(2)
        with col1:
            self.show_configs()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()


