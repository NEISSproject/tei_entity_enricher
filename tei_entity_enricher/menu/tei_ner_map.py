import streamlit as st
import json
import os

from tei_entity_enricher.util.helper import module_path, local_save_path
import tei_entity_enricher.menu.ner_task_def as ner_task


class TEINERMap():
    def __init__(self, state, show_menu=True):
        self.state = state

        self.tnm_Folder = 'TNM'
        self.template_tnm_Folder = os.path.join(module_path, 'templates', self.tnm_Folder)
        self.tnm_Folder = os.path.join(local_save_path, self.tnm_Folder)
        self.tnm_attr_name = 'name'
        self.tnm_attr_ntd = 'ntd'
        self.tnm_attr_template = 'template'
        self.tnm_attr_entity_dict = 'entity_dict'
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

        if show_menu:
            self.ntd = ner_task.NERTaskDef(state, show_menu=False)
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
            st.error(f'Choose another name. There is already a mapping with name {mapping[self.tnm_attr_name]}!')
        if val:
            mapping[self.tnm_attr_template] = False
            with open(os.path.join(self.tnm_Folder, mapping[self.tnm_attr_name].replace(' ', '_') + '.json'),
                      'w+') as f:
                json.dump(mapping, f)
            self.reset_tnm_edit_states()
            st.experimental_rerun()

    def validate_and_delete_mapping(self, mapping):
        val = True
        if val:
            os.remove(os.path.join(self.tnm_Folder, mapping[self.tnm_attr_name].replace(' ', '_') + '.json'))
            self.reset_tnm_edit_states()
            self.state.tnm_sel_mapping_name = None
            st.experimental_rerun()

    def reset_tnm_edit_states(self):
        self.state.tnm_name = None
        self.state.tnm_ntd_name = None
        self.state.tnm_entity_dict = None

    def show_editable_mapping_content(self, mode):
        if mode == self.tnm_mode_edit and len(self.editable_mapping_names) < 1:
            st.info(
                'There are no self-defined TEI NER Entity Mappings to edit in the moment. If you want to edit a template you have to duplicate it.')
        else:
            if self.state.tnm_mode != mode:
                self.reset_tnm_edit_states()
            self.state.tnm_mode = mode
            tnm_mapping_dict = {}
            init_tnm_ntd_name = self.state.tnm_ntd_name
            init_tnm_entity_dict = {}
            # init_use_notes=True
            if mode in [self.tnm_mode_dupl, self.tnm_mode_edit]:
                if self.tnm_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                selected_tnm_name = st.selectbox(f'Select a mapping to {mode}!', options, key='tnm' + mode)
                if self.state.tnm_sel_mapping_name != selected_tnm_name:
                    self.reset_tnm_edit_states()
                self.state.tnm_sel_mapping_name = selected_tnm_name
                tnm_mapping_dict = self.mappingdict[selected_tnm_name].copy()
                init_tnm_ntd_name = tnm_mapping_dict[self.tnm_attr_ntd][self.ntd.ntd_attr_name]
                init_tnm_entity_dict = tnm_mapping_dict[self.tnm_attr_entity_dict]
                if mode == self.tnm_mode_dupl:
                    tnm_mapping_dict[self.tnm_attr_name] = ''
            if mode == self.tnm_mode_add:
                tnm_mapping_dict[self.tnm_attr_ntd] = {}
                tnm_mapping_dict[self.tnm_attr_entity_dict] = {}
            if mode in [self.tnm_mode_dupl, self.tnm_mode_add]:
                self.state.tnm_name = st.text_input('New TEI NER Entity Mapping Name:', self.state.tnm_name or "")
                if self.state.tnm_name:
                    tnm_mapping_dict[self.tnm_attr_name] = self.state.tnm_name

            self.state.tnm_ntd_name = st.selectbox('Corresponding NER task definition', list(self.ntd.defdict.keys()),
                                                   list(self.ntd.defdict.keys()).index(
                                                       init_tnm_ntd_name) if init_tnm_ntd_name else 0,
                                                   key='tnm_ntd_sel' + mode)
            if self.state.tnm_ntd_name:
                tnm_edit_entity = st.selectbox('Define mapping for entity:',
                                               self.ntd.defdict[self.state.tnm_ntd_name][self.ntd.ntd_attr_entitylist],
                                               key='tnm_ent' + mode)
                if tnm_edit_entity:
                    self.state.tnm_entity_dict = self.edit_entity(mode, tnm_edit_entity, init_tnm_entity_dict)

            if st.button('Save TEI NER Entity Mapping', key=mode):
                tnm_mapping_dict[self.tnm_attr_ntd] = self.ntd.defdict[self.state.tnm_ntd_name]
                tnm_mapping_dict[self.tnm_attr_entity_dict] = self.state.tnm_entity_dict
                self.validate_and_saving_mapping(tnm_mapping_dict, mode)

    def edit_entity(self, mode, tnm_edit_entity, cur_entity_dict):
        if getattr(self.state, 'tnm' + self.state.tnm_ntd_name + tnm_edit_entity + mode):
            cur_entity_dict[tnm_edit_entity] = getattr(self.state,
                                                       'tnm' + self.state.tnm_ntd_name + tnm_edit_entity + mode)
        if tnm_edit_entity not in cur_entity_dict.keys():
            cur_entity_dict[tnm_edit_entity] = [[None, {}]]
        index = 0
        for mapping_entry in cur_entity_dict[tnm_edit_entity]:
            index += 1
            mapping_entry[0] = st.text_input('Tag ' + str(index), mapping_entry[0] or "",
                                             key='tnm' + self.state.tnm_ntd_name + tnm_edit_entity + mode + str(index))
        if st.button('Add another mapping'):
            cur_entity_dict[tnm_edit_entity].append([None, {}])
        setattr(self.state, 'tnm' + self.state.tnm_ntd_name + tnm_edit_entity + mode,
                cur_entity_dict[tnm_edit_entity])
        return cur_entity_dict

    def tei_ner_map_add(self):
        self.show_editable_mapping_content(self.tnm_mode_add)

    def tei_ner_map_dupl(self):
        self.show_editable_mapping_content(self.tnm_mode_dupl)

    def tei_ner_map_edit(self):
        self.show_editable_mapping_content(self.tnm_mode_edit)

    def tei_ner_map_del(self):
        selected_mapping_name = st.selectbox('Select a mapping to delete!', self.editable_mapping_names)
        if st.button('Delete Selected Mapping'):
            self.validate_and_delete_mapping(self.mappingdict[selected_mapping_name])

    def show_edit_environment(self):
        tnm_definer = st.beta_expander("Add or edit existing TEI NER Entity Mapping", expanded=False)
        with tnm_definer:
            options = {
                "Add TEI NER Entity Mapping": self.tei_ner_map_add,
                "Duplicate TEI NER Entity Mapping": self.tei_ner_map_dupl,
                "Edit TEI NER Entity Mapping": self.tei_ner_map_edit,
                "Delete TEI NER Entity Mapping": self.tei_ner_map_del
            }
            self.state.tnm_edit_options = st.radio("Edit Options", tuple(options.keys()), tuple(options.keys()).index(
                self.state.tnm_edit_options) if self.state.tnm_edit_options else 0)
            options[self.state.tnm_edit_options]()

    def show_test_environment(self):
        tnm_test_expander = st.beta_expander("Test TEI NER Entity Mapping", expanded=False)

    def build_tnm_tablestring(self):
        tablestring = 'Name | NER Task | Template \n -----|-------|-------'
        for mapping in self.mappingslist:
            if mapping[self.tnm_attr_template]:
                template = 'yes'
            else:
                template = 'no'
            tablestring += '\n ' + mapping[self.tnm_attr_name] + ' | ' + mapping[self.tnm_attr_ntd][
                self.ntd.ntd_attr_name] + ' | ' + template
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
