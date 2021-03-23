import streamlit as st
import tei_parser as tp
import json
import os

class Menu_tei_reader():
    def __init__(self,state):
        self.state=state

        self.config_Folder='TR_Configs'
        self.tr_config_attr_name='name'
        self.tr_config_attr_use_notes='use_notes'
        self.tr_config_mode_add='add'
        self.tr_config_mode_dupl='duplicate'
        self.tr_config_mode_edit='edit'

        configFilelist = os.listdir(self.config_Folder)
        self.configslist=[]
        for configFile in sorted(configFilelist):
            with open(os.path.join(self.config_Folder,configFile)) as f:
                self.configslist.append(json.load(f))
        self.configdict={}
        for config in self.configslist:
            self.configdict[config[self.tr_config_attr_name]]=config
        self.show()


    def validate_and_saving_config(self,config,mode):
        val=True
        if 'name' not in config.keys() or config[self.tr_config_attr_name] is None or config[self.tr_config_attr_name]=='':
            val=False
            st.warning('Please define a name for the config before saving!')
        elif os.path.isfile(os.path.join(self.config_Folder,config['name'].replace(' ','_')+'.json')) and mode!=self.tr_config_mode_edit:
            val=False
            st.warning('Choose another name. There is already a config with name ' + config[self.tr_config_attr_name] + '!')
        if val:
            with open(os.path.join(self.config_Folder,config[self.tr_config_attr_name].replace(' ','_')+'.json'),'w+') as f:
                json.dump(config,f)
            st.experimental_rerun()
            #st.success(config[tr_config_attr_name]+' saved.')

    def validate_and_delete_config(self,config):
        val=True
        if val:
            os.remove(os.path.join(self.config_Folder,config[self.tr_config_attr_name].replace(' ','_')+'.json'))
            st.experimental_rerun()


    def show_editable_config_content(self,mode):
        tr_config_dict={}
        init_use_notes=True
        if mode in [self.tr_config_mode_dupl,self.tr_config_mode_edit]:
            selected_config_name=st.selectbox('Select a config to '+mode+'!',list(self.configdict.keys()),key=mode)
            tr_config_dict=self.configdict[selected_config_name].copy()
            init_use_notes=tr_config_dict[self.tr_config_attr_use_notes]
            if mode==self.tr_config_mode_dupl:
                tr_config_dict[self.tr_config_attr_name]=''
        if mode in [self.tr_config_mode_dupl,self.tr_config_mode_add]:
            name=st.text_input('New TEI Reader Config Name:')
            if name:
                tr_config_dict[self.tr_config_attr_name]=name
        use_notes=st.checkbox('Tag Notes',init_use_notes)
        tr_config_dict[self.tr_config_attr_use_notes]=use_notes
        if st.button('Save',key=mode):
            self.validate_and_saving_config(tr_config_dict,mode)

    def teireaderadd(self):
        self.show_editable_config_content(self.tr_config_mode_add)

    def teireaderdupl(self):
        self.show_editable_config_content(self.tr_config_mode_dupl)

    def teireaderedit(self):
        self.show_editable_config_content(self.tr_config_mode_edit)

    def teireaderdel(self):
        selected_config_name=st.selectbox('Select a config to delete!',list(self.configdict.keys()))
        #st.json(configdict[selected_config_name])
        if st.button('Delete Selected Config'):
            self.validate_and_delete_config(self.configdict[selected_config_name])

    def show_edit_environment(self):
        tr_config_definer = st.beta_expander("Add or edit existing Config", expanded=False)
        with tr_config_definer:
            options = {
                "Add TEI Reader Config": self.teireaderadd,
                "Duplicate TEI Reader Config": self.teireaderdupl,
                "Edit TEI Reader Config": self.teireaderedit,
                "Delete TEI Reader Config": self.teireaderdel
                }
            self.state.tr_edit_options = st.radio("Edit Options", tuple(options.keys()),tuple(options.keys()).index(self.state.tr_edit_options) if self.state.tr_edit_options else 0)
            options[self.state.tr_edit_options]()

    def show_test_environment(self):
        tr_test_expander = st.beta_expander("Test TEI Reader Config", expanded=False)
        with tr_test_expander:
            selected_config_name=st.selectbox('Select a TEI Reader Config to test!',list(self.configdict.keys()),key='tr_test')
            config=self.configdict[selected_config_name]
            self.state.teifile = st.text_input('Choose a TEI File:', self.state.teifile or "")
            if self.state.teifile:
                tei=tp.tei_file(self.state.teifile,config)
                st.subheader('Text Content:')
                st.text(tei.get_text())
                if config[self.tr_config_attr_use_notes]:
                    st.subheader('Note Content:')
                    st.text(tei.get_notes())

    def build_config_tablestring(self):
        tablestring='Name | Tagging Notes \n -----|-------'
        for config in self.configslist:
            if config[self.tr_config_attr_use_notes]:
                use_notes='yes'
            else:
                use_notes='no'
            tablestring+='\n ' + config[self.tr_config_attr_name] + ' | ' + use_notes
        return tablestring


    def show_configs(self):
        tr_show_configs = st.beta_expander("Existing TEI Reader Configs", expanded=True)
        with tr_show_configs:
            st.markdown(self.build_config_tablestring())


    def show(self):
        st.title("TEI Reader Config")
        self.show_configs()
        self.show_edit_environment()
        self.show_test_environment()

if __name__ == '__main__':
    print(os.path.join('TR_Configs','test.json'))

