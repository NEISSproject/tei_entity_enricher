import streamlit as st
import tei_entity_enricher.util.tei_parser as tp
import json
import os

from tei_entity_enricher.util.helper import module_path


class TEINERMap():
    def __init__(self, state):
        self.state = state

        self.tnm_Folder = 'TNM'
        self.template_tnm_Folder = os.path.join(module_path, 'templates', self.tnm_Folder)
        self.tnm_attr_name = 'name'
        # self.tr_config_attr_excl_tags='exclude_tags'
        # self.tr_config_attr_use_notes='use_notes'
        # self.tr_config_attr_note_tags='note_tags'
        self.tnm_attr_template = 'template'
        self.tnm_mode_add = 'add'
        self.tnm_mode_dupl = 'duplicate'
        self.tnm_mode_edit = 'edit'

        if not os.path.isdir(self.tnm_Folder):
            os.mkdir(self.tnm_Folder)
        if not os.path.isdir(self.template_tnm_Folder):
            os.mkdir(self.template_tnm_Folder)

        self.mappingslist = []
        for mappingFile in sorted(os.listdir(self.template_tnm_Folder)):
            if mappingFile.endswith('json'):
                with open(os.path.join(self.template_tnm_Folder, mappingFile)) as f:
                    self.mappingslist.append(json.load(f))
        for mappingFile in sorted(os.listdir(self.tnm_Folder)):
            if mappingFile.endswith('json'):
                with open(os.path.join(self.tnm_Folder, mappingFile)) as f:
                    self.mappingslist.append(json.load(f))

        self.mappingdict = {}
        self.editable_mapping_names = []
        for mapping in self.mappingslist:
            self.mappingdict[mapping[self.tnm_attr_name]] = mapping
            if not mapping[self.tnm_attr_template]:
                self.editable_mapping_names.append(mapping[self.tnm_attr_name])

        self.show()

    def validate_and_saving_mapping(self, mapping, mode):
        val = True
        if self.tnm_attr_name not in mapping.keys() or mapping[self.tnm_attr_name] is None or mapping[
            self.tnm_attr_name] == '':
            val = False
            st.error('Please define a name for the mapping before saving!')
        elif os.path.isfile(os.path.join(self.tnm_Folder, mapping[self.tnm_attr_name].replace(' ',
                                                                                              '_') + '.json')) and mode != self.tnm_mode_edit:
            val = False
            st.error('Choose another name. There is already a mapping with name ' + mapping[self.tnm_attr_name] + '!')
        if val:
            mapping[self.tnm_attr_template] = False
            with open(os.path.join(self.tnm_Folder, mapping[self.tnm_attr_name].replace(' ', '_') + '.json'),
                      'w+') as f:
                json.dump(mapping, f)
            self.reset_tnm_edit_states()
            st.experimental_rerun()

    def reset_tnm_edit_states(self):
        self.state.tnm_name = None

    def show_editable_mapping_content(self, mode):
        if mode == self.tnm_mode_edit and len(self.editable_mapping_names) < 1:
            st.info(
                'There are no self-defined TEI NER Entity Mappings to edit in the moment. If you want to edit a template you have to duplicate it.')
        else:
            if self.state.tnm_mode != mode:
                self.reset_tnm_edit_states()
            self.state.tnm_mode = mode
            tnm_mapping_dict = {}
            # init_use_notes=True
            if mode in [self.tnm_mode_dupl, self.tnm_mode_edit]:
                if self.tnm_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                selected_tnm_name = st.selectbox('Select a mapping to ' + mode + '!', options, key=mode)
                if self.state.tnm_sel_mapping_name != selected_tnm_name:
                    self.reset_tnm_edit_states()
                self.state.tnm_sel_mapping_name = selected_tnm_name
                tnm_mapping_dict = self.mappingdict[selected_tnm_name].copy()
                if mode == self.tnm_mode_dupl:
                    tnm_mapping_dict[self.tnm_attr_name] = ''
            if mode in [self.tnm_mode_dupl, self.tnm_mode_add]:
                self.state.tnm_name = st.text_input('New TEI NER Entity Mapping Name:', self.state.tnm_name or "")
                if self.state.tnm_name:
                    tnm_mapping_dict[self.tnm_attr_name] = self.state.tnm_name
            if st.button('Save TEI NER Entity Mapping', key=mode):
                self.validate_and_saving_mapping(tnm_mapping_dict, mode)

    def teinermapadd(self):
        self.show_editable_mapping_content(self.tnm_mode_add)

    def teinermapdupl(self):
        self.show_editable_mapping_content(self.tnm_mode_dupl)

    def teinermapedit(self):
        self.show_editable_mapping_content(self.tnm_mode_edit)

    def teinermapdel(self):
        pass
        # selected_config_name=st.selectbox('Select a TEI NER Map to delete!',self.editable_config_names)
        # if st.button('Delete Selected Config'):
        #    self.validate_and_delete_config(self.configdict[selected_config_name])

    def show_edit_environment(self):
        tnm_definer = st.beta_expander("Add or edit existing TEI NER Entity Mapping", expanded=False)
        with tnm_definer:
            options = {
                "Add TEI NER Entity Mapping": self.teinermapadd,
                "Duplicate TEI NER Entity Mapping": self.teinermapdupl,
                "Edit TEI NER Entity Mapping": self.teinermapedit,
                "Delete TEI NER Entity Mapping": self.teinermapdel
            }
            self.state.tnm_edit_options = st.radio("Edit Options", tuple(options.keys()), tuple(options.keys()).index(
                self.state.tnm_edit_options) if self.state.tnm_edit_options else 0)
            options[self.state.tnm_edit_options]()

    def show_test_environment(self):
        tnm_test_expander = st.beta_expander("Test TEI NER Entity Mapping", expanded=False)

    def build_tnm_tablestring(self):
        tablestring = 'Name | Template \n -----|-------'
        for mapping in self.mappingslist:
            if mapping[self.tnm_attr_template]:
                template = 'yes'
            else:
                template = 'no'
            tablestring += '\n ' + mapping[self.tnm_attr_name] + ' | ' + template
        return tablestring

    def show_tnms(self):
        tnm_show = st.beta_expander("Existing TEI NER Entity Mappings", expanded=True)
        with tnm_show:
            st.markdown(self.build_tnm_tablestring())

    def show(self):
        st.latex('\\text{\Huge{TEI NER Entity Mapping}}')
        col1, col2 = st.beta_columns(2)
        with col1:
            self.show_tnms()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
