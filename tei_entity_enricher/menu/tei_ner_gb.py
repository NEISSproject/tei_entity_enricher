import streamlit as st
import json
import os

from tei_entity_enricher.util.helper import module_path, local_save_path
import tei_entity_enricher.menu.tei_ner_map as tei_map
import tei_entity_enricher.menu.tei_reader as tei_reader

class TEINERGroundtruthBuilder():
    def __init__(self, state, show_menu=True):
        self.state = state

        self.tng_Folder = 'TNG'
        #self.template_tng_Folder = os.path.join(module_path, 'templates', self.tnm_Folder)
        self.tng_Folder = os.path.join(local_save_path, self.tng_Folder)
        self.tng_attr_name = 'name'
        self.tng_attr_tr = 'tr'
        self.tng_attr_tnm = 'tnm'
        self.tng_attr_ratio = 'ratio'
        self.tng_attr_shuffle_type = 'shuffle_type'

        if not os.path.isdir(self.tng_Folder):
            os.mkdir(self.tng_Folder)
        #if not os.path.isdir(self.template_tng_Folder):
        #    os.mkdir(self.template_tng_Folder)

        #self.mappingslist = []
        #for mappingFile in sorted(os.listdir(self.template_tnm_Folder)):
        #    if mappingFile.endswith('json'):
        #        with open(os.path.join(self.template_tnm_Folder, mappingFile)) as f:
        #            self.mappingslist.append(json.load(f))
        #for mappingFile in sorted(os.listdir(self.tnm_Folder)):
        #    if mappingFile.endswith('json'):
        #        with open(os.path.join(self.tnm_Folder, mappingFile)) as f:
        #            self.mappingslist.append(json.load(f))

        #self.mappingdict = {}
        #self.editable_mapping_names = []
        #for mapping in self.mappingslist:
        #    self.mappingdict[mapping[self.tnm_attr_name]] = mapping
        #    if not mapping[self.tnm_attr_template]:
        #        self.editable_mapping_names.append(mapping[self.tnm_attr_name])

        if show_menu:
            self.tnm = tei_map.TEINERMap(state, show_menu=False)
            self.tr = tei_reader.TEIReader(state, show_menu=False)
            self.show()

    def show(self):
        st.latex('\\text{\Huge{TEI NER Groundtruth Builder}}')
        #col1, col2 = st.beta_columns(2)
        #with col1:
        #    self.show_tnms()
        #with col2:
        #    self.show_edit_environment()
        #self.show_test_environment()
