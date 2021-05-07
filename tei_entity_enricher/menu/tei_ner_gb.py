import streamlit as st
import json
import os
import spacy

from tei_entity_enricher.util.helper import module_path, local_save_path
import tei_entity_enricher.menu.tei_ner_map as tei_map
import tei_entity_enricher.menu.tei_reader as tei_reader


class TEINERGroundtruthBuilder():
    def __init__(self, state, show_menu=True):
        self.state = state

        self.tng_Folder = 'TNG'
        # self.template_tng_Folder = os.path.join(module_path, 'templates', self.tnm_Folder)
        self.tng_Folder = os.path.join(local_save_path, self.tng_Folder)
        self.tng_attr_name = 'name'
        self.tng_attr_tr = 'tr'
        self.tng_attr_tnm = 'tnm'
        self.tng_attr_lang = 'lang'
        self.tng_attr_ratio = 'ratio'
        self.tng_attr_shuffle_type = 'shuffle_type'

        self.lang_dict = {'German': 'de_core_news_sm', 'English': 'en_core_web_sm', 'Multilingual': 'xx_ent_wiki_sm',
                          'French': 'fr_core_news_sm', 'Spanish': 'es_core_news_sm'}
        self.shuffle_options_dict = {'Shuffle by TEI File': 'shufFile', 'Shuffle by Sentences': 'shufSent'}

        if not os.path.isdir(self.tng_Folder):
            os.mkdir(self.tng_Folder)
        # if not os.path.isdir(self.template_tng_Folder):
        #    os.mkdir(self.template_tng_Folder)

        # self.mappingslist = []
        # for mappingFile in sorted(os.listdir(self.template_tnm_Folder)):
        #    if mappingFile.endswith('json'):
        #        with open(os.path.join(self.template_tnm_Folder, mappingFile)) as f:
        #            self.mappingslist.append(json.load(f))
        # for mappingFile in sorted(os.listdir(self.tnm_Folder)):
        #    if mappingFile.endswith('json'):
        #        with open(os.path.join(self.tnm_Folder, mappingFile)) as f:
        #            self.mappingslist.append(json.load(f))

        # self.mappingdict = {}
        # self.editable_mapping_names = []
        # for mapping in self.mappingslist:
        #    self.mappingdict[mapping[self.tnm_attr_name]] = mapping
        #    if not mapping[self.tnm_attr_template]:
        #        self.editable_mapping_names.append(mapping[self.tnm_attr_name])

        if show_menu:
            self.tnm = tei_map.TEINERMap(state, show_menu=False)
            self.tr = tei_reader.TEIReader(state, show_menu=False)
            self.show()

    def get_spacy_lm(self, lang):
        if not spacy.util.is_package(self.lang_dict[lang]):
            spacy.cli.download(self.lang_dict[lang])
        return spacy.load(self.lang_dict[lang])

    def show_build_gt_environment(self):
        tng_dict = {}
        col1, col2 = st.beta_columns(2)
        with col1:
            self.state.tng_name = st.text_input('Define a name for the groundtruth:', self.state.tng_name or "")
            if self.state.tng_name:
                tng_dict[self.tng_attr_name] = self.state.tnm_name
            self.state.tng_lang = st.selectbox(
                'Select a language for the groundtruth (relevant for the split into sentences):',
                list(self.lang_dict.keys()), list(self.lang_dict.keys()).index(
                    self.state.tng_lang) if self.state.tng_lang else 0, key='tng_lang')
            if self.state.tng_lang:
                tng_dict[self.tng_attr_lang] = self.state.tng_lang
        with col2:
            self.state.tng_tr_name = st.selectbox('Select a TEI Reader Config for Building the groundtruth:',
                                                  list(self.tr.configdict.keys()),
                                                  list(self.tr.configdict.keys()).index(
                                                      self.state.tng_tr_name) if self.state.tng_tr_name else 0,
                                                  key='tng_tr')
            if self.state.tng_tr_name:
                tng_dict[self.tng_attr_tr] = self.tr.configdict[self.state.tng_tr_name]
            self.state.tng_tnm_name = st.selectbox('Select a TEI NER Entity Mapping for Building the groundtruth:',
                                                   list(self.tnm.mappingdict.keys()),
                                                   list(self.tnm.mappingdict.keys()).index(
                                                       self.state.tng_tnm_name) if self.state.tng_tnm_name else 0,
                                                   key='tng_tnm')
            if self.state.tng_tnm_name:
                tng_dict[self.tng_attr_tnm] = self.tnm.mappingdict[self.state.tng_tnm_name]

        col3, col4 = st.beta_columns(2)
        col5, col6, col7 = st.beta_columns([0.25, 0.25, 0.5])
        with col3:
            st.markdown('Define a ratio for the partition into train- development- and testset.')
        # with col4:
        # self.state.tng_shuffle_options = st.radio("Shuffle Options", tuple(self.shuffle_options_dict.keys()),
        #                                          tuple(self.shuffle_options_dict.keys()).index(
        #                                              self.state.tng_shuffle_options) if self.state.tng_shuffle_options else 0)
        # tng_dict[self.tng_attr_shuffle_type] = self.state.tng_shuffle_options
        with col5:
            self.state.tng_test_percentage = st.number_input('Percentage for the test set', min_value=0,
                                                             max_value=100 - (
                                                                 self.state.tng_dev_percentage if self.state.tng_dev_percentage else 10),
                                                             value=self.state.tng_test_percentage if self.state.tng_test_percentage else 10)
        with col6:
            self.state.tng_dev_percentage = st.number_input('Percentage for the validation set', min_value=0,
                                                            max_value=100 - (
                                                                self.state.tng_test_percentage if self.state.tng_test_percentage else 10),
                                                            value=self.state.tng_dev_percentage if self.state.tng_dev_percentage else 10)
        with col7:
            self.state.tng_shuffle_options = st.radio("Shuffle Options", tuple(self.shuffle_options_dict.keys()),
                                                      tuple(self.shuffle_options_dict.keys()).index(
                                                          self.state.tng_shuffle_options) if self.state.tng_shuffle_options else 0)
            tng_dict[self.tng_attr_shuffle_type] = self.state.tng_shuffle_options
        col8, col9 = st.beta_columns(2)
        with col8:
            st.write('With this configuration you have ',
                     100 - self.state.tng_dev_percentage - self.state.tng_test_percentage,
                     '% of the data for the train set, ', self.state.tng_dev_percentage,
                     '% for the development set and',
                     self.state.tng_test_percentage, '% for the test set.')
        self.state.tng_teifile_folder = st.text_input(
            'Choose a Folder containing only TEI Files to build the groundtruth from:',
            self.state.tng_teifile_folder if self.state.tng_teifile_folder else "",
            key='tng_tei_file_folder')
        tng_dict[self.tng_attr_ratio] = {'train': 100 - self.state.tng_dev_percentage - self.state.tng_test_percentage,
                                         'dev': self.state.tng_dev_percentage, 'test': self.state.tng_test_percentage}
        if st.button('Build Groundtruth'):
            pass

    def show(self):
        st.latex('\\text{\Huge{TEI NER Groundtruth Builder}}')
        tng_build_new = st.beta_expander("Build new TEI NER Groundtruth", expanded=False)
        with tng_build_new:
            self.show_build_gt_environment()
        tng_delete = st.beta_expander("Delete existing TEI NER Groundtruth", expanded=False)
        with tng_delete:
            pass
        tng_show = st.beta_expander("Show existing TEI NER Groundtruth", expanded=True)
        with tng_show:
            pass
