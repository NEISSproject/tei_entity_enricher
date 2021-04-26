import streamlit as st
import TEIEntityEnricher.tei_parser as tp
import json
import os
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

class Menu_ner_tei_reader():
    def __init__(self,state):
        self.state=state

        #self.config_Folder='TR_Configs'
        #self.template_config_Folder=os.path.join('TEIEntityEnricher','Templates',self.config_Folder)
        #self.tr_config_attr_name='name'
        #self.tr_config_attr_excl_tags='exclude_tags'
        #self.tr_config_attr_use_notes='use_notes'
        #self.tr_config_attr_note_tags='note_tags'
        #self.tr_config_attr_template='template'
        #self.tr_config_mode_add='add'
        #self.tr_config_mode_dupl='duplicate'
        #self.tr_config_mode_edit='edit'

        self.show()



    def show_edit_environment(self):
        tr_config_definer = st.beta_expander("Add or edit existing NER Config", expanded=False)


    def show_test_environment(self):
        tr_test_expander = st.beta_expander("Test TEI NER Reader Config", expanded=False)


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
        tr_show_configs = st.beta_expander("Existing TEI NER Reader Configs", expanded=True)



    def show(self):
        st.latex('\\text{\Huge{TEI NER Reader Config}}')
        col1, col2 = st.beta_columns(2)
        with col1:
            self.show_configs()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()


