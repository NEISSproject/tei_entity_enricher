import streamlit as st
import tei_parser as tp
import json
import os
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

class Menu_tei_reader():
    def __init__(self,state):
        self.state=state

        self.config_Folder='TR_Configs'
        self.tr_config_attr_name='name'
        self.tr_config_attr_use_notes='use_notes'
        self.tr_config_attr_excl_tags='exclude_tags'
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

    def show_editable_exclude_tags(self,excl_list,mode,name):
        #excl_options=['Add','Delete']
        #col1, col2 = st.beta_columns(2)
        #self.state.excl_radio=col1.radio('Exclude Tags',['Add','Delete'],excl_options.index(self.state.excl_radio) if self.state.excl_radio else 0)
        #if self.state.excl_radio == 'Add':
        #    tr_excl_tag=col2.text_input('Exclude Tag to add:')
        #    if col2.button('Add to Exclude List'):
        #        excl_list.append(tr_excl_tag)
        #elif self.state.excl_radio == 'Delete':
        #    tr_excl_selbox=col2.selectbox('Remove Exclude Tag from excluding list:',excl_list, 0)
        #    if col2.button('Remove from Exclude List'):
        #        excl_list.remove(tr_excl_selbox)
        st.markdown('Define Tags to Exclude from the text which should be considered.')
        response = AgGrid(
            pd.DataFrame({'Exclude': excl_list+['']*100}),#input_dataframe,
            height=200,
            editable=True,
            sortable=False,
            filter=False,
            resizable=True,
            defaultWidth=1,
            fit_columns_on_grid_load=True,
            key=mode+name)
        st.info('Edit the table by double-click in it and press Enter after changing a cell.')
        if 'data' in response:
            all_list=list(response['data'].to_dict()['Exclude'].values())
            returnlist=[]
            for element in all_list:
                if element!='' and element is not None:
                    returnlist.append(element)
        return returnlist

    def get_listoutput(self,list):
        output=""
        for element in list:
            output+=element+', '
        if len(list)>0:
            output=output[:-2]
        return output


    def show_editable_config_content(self,mode):
        if self.state.tr_mode!=mode:
            self.state.tr_exclude_list=None
        self.state.tr_mode=mode
        tr_config_dict={}
        init_use_notes=True
        if mode in [self.tr_config_mode_dupl,self.tr_config_mode_edit]:
            selected_config_name=st.selectbox('Select a config to '+mode+'!',list(self.configdict.keys()),key=mode)
            if self.state.tr_sel_config_name!=selected_config_name:
                self.state.tr_exclude_list=None
            self.state.tr_sel_config_name=selected_config_name
            tr_config_dict=self.configdict[selected_config_name].copy()
            init_use_notes=tr_config_dict[self.tr_config_attr_use_notes]
            if mode==self.tr_config_mode_dupl:
                tr_config_dict[self.tr_config_attr_name]=''
        if mode in [self.tr_config_mode_dupl,self.tr_config_mode_add]:
            tr_config_dict[self.tr_config_attr_excl_tags]=[]
            name=st.text_input('New TEI Reader Config Name:')
            if name:
                tr_config_dict[self.tr_config_attr_name]=name
        init_exclude_list=tr_config_dict[self.tr_config_attr_excl_tags]


        self.state.tr_exclude_list=self.show_editable_exclude_tags(self.state.tr_exclude_list if self.state.tr_exclude_list else init_exclude_list,mode,tr_config_dict[self.tr_config_attr_name] if self.tr_config_attr_name in tr_config_dict.keys() else '')
        #st.write('Tags to exclude: '+ self.get_listoutput(self.state.tr_exclude_list))
        use_notes=st.checkbox('Tag Notes',init_use_notes)
        tr_config_dict[self.tr_config_attr_use_notes]=use_notes
        if st.button('Save',key=mode):
            tr_config_dict[self.tr_config_attr_excl_tags]=self.state.tr_exclude_list
            self.state.tr_exclude_list=None
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
        tablestring='Name | Exclude Tags | Tagging Notes \n -----|-------|-------'
        for config in self.configslist:
            if config[self.tr_config_attr_use_notes]:
                use_notes='yes'
            else:
                use_notes='no'
            tablestring+='\n ' + config[self.tr_config_attr_name] + ' | ' + self.get_listoutput(config[self.tr_config_attr_excl_tags]) +  ' | ' + use_notes
        return tablestring


    def show_configs(self):
        tr_show_configs = st.beta_expander("Existing TEI Reader Configs", expanded=True)
        with tr_show_configs:
            st.markdown(self.build_config_tablestring())


    def show(self):
        st.latex('\\text{\Huge{TEI Reader Config}}')
        self.show_configs()
        self.show_edit_environment()
        self.show_test_environment()

if __name__ == '__main__':
    print(os.path.join('TR_Configs','test.json'))

