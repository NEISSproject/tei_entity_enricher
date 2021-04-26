import streamlit as st
import json
import os
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

class Menu_ner_task_def():
    def __init__(self,state):
        self.state=state

        self.ntd_Folder='NTD'
        self.template_ntd_Folder=os.path.join('TEIEntityEnricher','Templates',self.ntd_Folder)
        self.ntd_attr_name='name'
        self.ntd_attr_entitylist='entitylist'
        self.ntd_attr_template='template'
        self.ntd_mode_add='add'
        self.ntd_mode_dupl='duplicate'
        self.ntd_mode_edit='edit'

        if not os.path.isdir(self.ntd_Folder):
            os.mkdir(self.ntd_Folder)
        if not os.path.isdir(self.template_ntd_Folder):
            os.mkdir(self.template_ntd_Folder)

        self.defslist=[]
        for defFile in sorted(os.listdir(self.template_ntd_Folder)):
            if defFile.endswith('json'):
                with open(os.path.join(self.template_ntd_Folder,defFile)) as f:
                    self.defslist.append(json.load(f))
        for defFile in sorted(os.listdir(self.ntd_Folder)):
            if defFile.endswith('json'):
                with open(os.path.join(self.ntd_Folder,defFile)) as f:
                    self.defslist.append(json.load(f))

        self.defdict={}
        self.editable_def_names=[]
        for definition in self.defslist:
            self.defdict[definition[self.ntd_attr_name]]=definition
            if not definition[self.ntd_attr_template]:
                self.editable_def_names.append(definition[self.ntd_attr_name])

        self.show()

    def validate_and_saving_definition(self, definition, mode):
        val=True
        if self.ntd_attr_name not in definition.keys() or definition[self.ntd_attr_name] is None or definition[self.ntd_attr_name]== '':
            val=False
            st.error('Please define a name for the definition before saving!')
        elif os.path.isfile(os.path.join(self.ntd_Folder, definition[self.ntd_attr_name].replace(' ', '_') + '.json')) and mode!=self.ntd_mode_edit:
            val=False
            st.error('Choose another name. There is already a definition with name ' + definition[self.ntd_attr_name] + '!')
        if val:
            definition[self.ntd_attr_template]=False
            with open(os.path.join(self.ntd_Folder, definition[self.ntd_attr_name].replace(' ', '_') + '.json'), 'w+') as f:
                json.dump(definition, f)
            self.reset_ntd_edit_states()
            st.experimental_rerun()

    def validate_and_delete_definition(self,definition):
        val=True
        if val:
            os.remove(os.path.join(self.ntd_Folder,definition[self.ntd_attr_name].replace(' ','_')+'.json'))
            self.reset_ntd_edit_states()
            self.state.ntd_sel_definition_name=None
            st.experimental_rerun()

    def show_editable_entitylist(self, entitylist, mode, name):
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
        st.markdown('Define a list of entities for the ner task.')
        response = AgGrid(
            pd.DataFrame({'Entities': entitylist + [''] * 100}),#input_dataframe,
            height=150,
            editable=True,
            sortable=False,
            filter=False,
            resizable=True,
            defaultWidth=1,
            fit_columns_on_grid_load=True,
            key='ntd_entitylist'+mode+name)
        st.info('Edit the table by double-click in it and press Enter after changing a cell.')
        returnlist=[]
        if 'data' in response:
            all_list=list(response['data'].to_dict()['Entities'].values())
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
        else:
            output=""
        return output

    def reset_ntd_edit_states(self):
        self.state.ntd_name=None
        self.state.ntd_entitylist=None

    def show_editable_definition_content(self,mode):
        if mode==self.ntd_mode_edit and len(self.editable_def_names)<1:
            st.info('There are no self-defined NER Task Entity Definitions to edit in the moment. If you want to edit a template you have to duplicate it.')
        else:
            if self.state.ntd_mode!=mode:
                self.reset_ntd_edit_states()
            self.state.ntd_mode=mode
            ntd_definition_dict={}
            #init_use_notes=True
            if mode in [self.ntd_mode_dupl,self.ntd_mode_edit]:
                if self.ntd_mode_dupl==mode:
                    options=list(self.defdict.keys())
                else:
                    options=self.editable_def_names
                selected_ntd_name=st.selectbox('Select a definition to '+mode+'!',options,key=mode)
                if self.state.ntd_sel_definition_name!=selected_ntd_name:
                    self.reset_ntd_edit_states()
                self.state.ntd_sel_definition_name=selected_ntd_name
                ntd_definition_dict=self.defdict[selected_ntd_name].copy()
                if mode==self.ntd_mode_dupl:
                    ntd_definition_dict[self.ntd_attr_name]=''
            if mode==self.ntd_mode_add:
                ntd_definition_dict[self.ntd_attr_entitylist]=[]
            if mode in [self.ntd_mode_dupl,self.ntd_mode_add]:
                self.state.ntd_name=st.text_input('New NER Task Entity Definition Name:',self.state.ntd_name or "")
                if self.state.ntd_name:
                    ntd_definition_dict[self.ntd_attr_name]=self.state.ntd_name
            init_entitylist=ntd_definition_dict[self.ntd_attr_entitylist]

            self.state.ntd_entitylist=self.show_editable_entitylist(self.state.ntd_entitylist if self.state.ntd_entitylist else init_entitylist,mode,selected_ntd_name if mode!=self.ntd_mode_add else '')
            if st.button('Save NER Task Entity Definition',key=mode):
                ntd_definition_dict[self.ntd_attr_entitylist]=self.state.ntd_entitylist
                self.validate_and_saving_definition(ntd_definition_dict,mode)

    def teinermapadd(self):
        self.show_editable_definition_content(self.ntd_mode_add)

    def teinermapdupl(self):
        self.show_editable_definition_content(self.ntd_mode_dupl)

    def teinermapedit(self):
        self.show_editable_definition_content(self.ntd_mode_edit)

    def teinermapdel(self):
        selected_definition_name=st.selectbox('Select a definition to delete!',self.editable_def_names)
        if st.button('Delete Selected Definition'):
            self.validate_and_delete_definition(self.defdict[selected_definition_name])

    def show_edit_environment(self):
        ntd_definer = st.beta_expander("Add or edit existing NER Task Entity Definition", expanded=False)
        with ntd_definer:
            options = {
                "Add NER Task Entity Definition": self.teinermapadd,
                "Duplicate NER Task Entity Definition": self.teinermapdupl,
                "Edit NER Task Entity Definition": self.teinermapedit,
                "Delete NER Task Entity Definition": self.teinermapdel
                }
            self.state.ntd_edit_options = st.radio("Edit Options", tuple(options.keys()),tuple(options.keys()).index(self.state.ntd_edit_options) if self.state.ntd_edit_options else 0)
            options[self.state.ntd_edit_options]()



    def build_ntd_tablestring(self):
        tablestring='Name | Exclude Tags | Template \n -----|-------|-------'
        for definition in self.defslist:
            if definition[self.ntd_attr_template]:
                template='yes'
            else:
                template='no'
            tablestring+='\n ' + definition[self.ntd_attr_name] + ' | ' + self.get_listoutput(definition[self.ntd_attr_entitylist]) + ' | ' + template
        return tablestring

    def show_ntds(self):
        ntd_show = st.beta_expander("Existing NER Task Entity Definitions", expanded=True)
        with ntd_show:
            st.markdown(self.build_ntd_tablestring())



    def show(self):
        st.latex('\\text{\Huge{NER Task Entity Definition}}')
        self.show_ntds()
        self.show_edit_environment()


