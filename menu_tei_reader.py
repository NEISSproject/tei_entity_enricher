import streamlit as st
import tei_parser as tp
import json
import os

config_Folder='TR_Configs'
tr_config_attr_name='name'
tr_config_attr_use_notes='use_notes'
tr_config_mode_add='add'
tr_config_mode_dupl='duplicate'
tr_config_mode_edit='edit'

def validate_and_saving_config(config,mode):
    val=True
    if 'name' not in config.keys() or config[tr_config_attr_name] is None or config[tr_config_attr_name]=='':
        val=False
        st.warning('Please define a name for the config before saving!')
    elif os.path.isfile(os.path.join(config_Folder,config['name'].replace(' ','_')+'.json')) and mode!=tr_config_mode_edit:
        val=False
        st.warning('Choose another name. There is already a config with name ' + config[tr_config_attr_name] + '!')
    if val:
        with open(os.path.join(config_Folder,config[tr_config_attr_name].replace(' ','_')+'.json'),'w+') as f:
            json.dump(config,f)
        st.experimental_rerun()
        #st.success(config[tr_config_attr_name]+' saved.')

def validate_and_delete_config(config):
    val=True
    if val:
        os.remove(os.path.join(config_Folder,config[tr_config_attr_name].replace(' ','_')+'.json'))
        st.experimental_rerun()


def show_editable_config_content(configslist,mode=tr_config_mode_add):
    configdict={}
    tr_config_dict={}
    for config in configslist:
        configdict[config[tr_config_attr_name]]=config
    if mode in [tr_config_mode_dupl,tr_config_mode_edit]:
        selected_config_name=st.selectbox('Select a config to '+mode+'!',list(configdict.keys()))
        tr_config_dict=configdict[selected_config_name]
        if mode==tr_config_mode_dupl:
            tr_config_dict[tr_config_attr_name]=''
    if mode in [tr_config_mode_dupl,tr_config_mode_add]:
        name=st.text_input('New TEI Reader Config Name:')
        if name:
            tr_config_dict[tr_config_attr_name]=name
    use_notes=st.checkbox('Tag Notes',True)
    tr_config_dict[tr_config_attr_use_notes]=use_notes
    if st.button('Save'):
        validate_and_saving_config(tr_config_dict,mode)

def teireaderadd(state,configslist):
    show_editable_config_content(configslist,tr_config_mode_add)

def teireaderdupl(state,configslist):
    show_editable_config_content(configslist,tr_config_mode_dupl)

def teireaderedit(state,configslist):
    show_editable_config_content(configslist,tr_config_mode_edit)

def teireaderdel(state,configslist):
    configdict={}
    for config in configslist:
        configdict[config[tr_config_attr_name]]=config
    selected_config_name=st.selectbox('Select a config to delete!',list(configdict.keys()))
    #st.json(configdict[selected_config_name])
    if st.button('Delete Selected Config'):
        validate_and_delete_config(configdict[selected_config_name])



def show_edit_environment(state,configslist):
    tr_config_definer = st.beta_expander("Add or edit existing Config", expanded=False)
    with tr_config_definer:
        options = {
            "Add TEI Reader Config": teireaderadd,
            "Duplicate TEI Reader Config": teireaderdupl,
            "Edit TEI Reader Config": teireaderedit,
            "Delete TEI Reader Config": teireaderdel
            }
        state.tr_edit_options = st.radio("Edit Options", tuple(options.keys()),tuple(options.keys()).index(state.tr_edit_options) if state.tr_edit_options else 0)
        options[state.tr_edit_options](state,configslist)

def show_test_environment(state):
    tr_test_expander = st.beta_expander("Test TEI Reader Config", expanded=False)
    with tr_test_expander:
        state.teifile = st.text_input('Choose a TEI File:', state.teifile or "")
        if state.teifile:
            tei=tp.tei_file(state.teifile)
            st.subheader('Text Content:')
            st.text(tei.get_text())
            st.subheader('Note Content:')
            st.text(tei.get_notes())

def build_config_tablestring(configslist):
    tablestring='Name | Tagging Notes \n -----|-------'
    for config in configslist:
        if config[tr_config_attr_use_notes]:
            use_notes='yes'
        else:
            use_notes='no'
        tablestring+='\n ' + config[tr_config_attr_name] + ' | ' + use_notes
    return tablestring


def show_configs(configslist):
    tr_show_configs = st.beta_expander("Existing TEI Reader Configs", expanded=True)
    with tr_show_configs:
        st.markdown(build_config_tablestring(configslist))


def show(state):
    st.title("TEI Reader Config")
    configFilelist = os.listdir(config_Folder)
    configslist=[]
    for configFile in sorted(configFilelist):
        with open(os.path.join(config_Folder,configFile)) as f:
            configslist.append(json.load(f))
    show_configs(configslist)
    show_edit_environment(state,configslist)
    show_test_environment(state)

if __name__ == '__main__':
    print(os.path.join('TR_Configs','test.json'))

