import streamlit as st
import json
import os
from tei_entity_enricher.util.helper import (
    local_save_path,
    makedir_if_necessary,
)
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector
from streamlit_ace import st_ace

import tei_entity_enricher.menu.ner_task_def as ner_task


class SparQLDef:
    def __init__(self, show_menu=True):
        self.sds_Folder = os.path.join(local_save_path,"config","postprocessing")
        self.sds_mode_add = "add"
        self.sds_mode_dupl = "duplicate"
        self.sds_mode_edit = "edit"
        if "sds_ace_key_counter" not in st.session_state:
            st.session_state.sds_ace_key_counter = 0
        self.check_one_time_attributes()

        makedir_if_necessary(self.sds_Folder)
        self.init_sparql_list()

        if show_menu:
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.show()

    def init_sparql_list(self):
        self.sds_path=os.path.join(self.sds_Folder,"self_def_sparql_queries.json")
        if not os.path.isfile(self.sds_path):
            with open(self.sds_path,"w+") as f:
                    json.dump({}, f)
        self.sds_template_path=os.path.join(self.sds_Folder,"sparql_queries.json")
        if not os.path.isfile(self.sds_template_path):
            #Initialize Wikidata_Connector to build sparql_query templates:
            WikidataConnector()

        with open(self.sds_path) as f:
            sparqldict=json.load(f)
        self.editable_sparql_names = list(sparqldict.keys())
        with open(self.sds_template_path) as f:
            self.sparqldict=json.load(f)
        self.sparqldict.update(sparqldict)




    def check_one_time_attributes(self):
        if "sds_save_message" in st.session_state and st.session_state.sds_save_message is not None:
            self.sds_save_message = st.session_state.sds_save_message
            st.session_state.sds_save_message = None
        else:
            self.sds_save_message = None



    def validate_for_saving_sparql(self, name,content, mode):
        val = True
        if (
             name is None
            or name == ""
        ):
            val = False
            st.error("Please define a name for the SparQL Query before saving!")
        elif name in self.sparqldict.keys() and mode != self.sds_mode_edit:
            val = False
            st.error(f"Choose another name. There is already a SparQL Query with name {name}!")
        return val

    def validate_definition_for_delete(self, name, content):
        val = True
        for definition in self.ntd.defslist:
            if self.ntd.ntd_attr_sparql_map in definition.keys():
                for entity in definition[self.ntd.ntd_attr_sparql_map].keys():
                    if definition[self.ntd.ntd_attr_sparql_map][entity]==name:
                        val = False
                        st.error(f'Deletion of the SparQL Query {name} is not allowed, because it is already used in the NER Task Entity definition {definition[self.ntd.ntd_attr_name]}. If necessary first remove the assignment of the SparQL Query from the NER Task')
        return val

    def reload_ace_components(self):
        st.session_state.sds_ace_key_counter+=1

    def show_editable_sparql_content(self, mode):
        if mode == self.sds_mode_edit and len(self.editable_sparql_names) < 1:
            st.info(
                "There are no self-defined SparQL Queries to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            if mode in [self.sds_mode_dupl, self.sds_mode_edit]:
                if self.sds_mode_dupl == mode:
                    options = list(self.sparqldict.keys())
                else:
                    options = self.editable_sparql_names
                st.selectbox(
                    f"Select a SparQL Query to {mode}!",
                    options,
                    index=0,
                    key="sds_sel_query_name_" + mode,
                    on_change=self.reload_ace_components
                )
                cur_query_content = self.sparqldict[st.session_state["sds_sel_query_name_" + mode]].copy()
                cur_query_name=st.session_state["sds_sel_query_name_" + mode]
                if mode == self.sds_mode_dupl:
                    cur_query_name = ""
            if mode == self.sds_mode_add:
                cur_query_content = ["",""]
            if mode in [self.sds_mode_dupl, self.sds_mode_add]:
                st.text_input(label="New SparQL Query Name:", key="sds_name_" + mode)
                cur_query_name = st.session_state["sds_name_" + mode]
            st.markdown("Define the SparQL Query:")
            query_content = st_ace(
                    value=cur_query_content[0],
                    height=200,
                    language="sparql",
                    readonly=False,
                    key="sds_ace_query_key" + str(st.session_state.sds_ace_key_counter),
                )
            if query_content!=cur_query_content[0]:
                cur_query_content[0]= query_content
            st.markdown("Comment:")
            comment_content = st_ace(
                    value=cur_query_content[1],
                    height=200,
                    readonly=False,
                    key="sds_ace_comment_key" + str(st.session_state.sds_ace_key_counter),
                )
            if comment_content!=cur_query_content[1]:
                cur_query_content[1]= comment_content
            def save_sds(cur_name, cur_content, mode):
                new_sparqldict={}
                for name in self.editable_sparql_names:
                    new_sparqldict[name]=self.sparqldict[name]
                new_sparqldict[cur_name]=cur_content
                with open(self.sds_path,"w+") as f:
                    json.dump(new_sparqldict, f,indent=4)

                st.session_state.sds_save_message = (
                    f"SparQL Query {cur_name} succesfully saved!"
                )
                if mode != self.sds_mode_edit:
                    st.session_state["sds_name_" + mode] = ""
                #del st.session_state["sds_show_query_name"]
                st.session_state.sds_ace_key_counter+=1

            if self.validate_for_saving_sparql(cur_query_name,cur_query_content, mode):
                st.button(
                    "Save SparQL Query",
                    on_click=save_sds,
                    args=(
                        cur_query_name,
                        cur_query_content,
                        mode,
                    ),
                )

    def sparql_add(self):
        self.show_editable_sparql_content(self.sds_mode_add)

    def sparql_dupl(self):
        self.show_editable_sparql_content(self.sds_mode_dupl)

    def sparql_edit(self):
        self.show_editable_sparql_content(self.sds_mode_edit)

    def sparql_del(self):
        def delete_sds(sparql_name):
            new_sparqldict={}
            for name in self.editable_sparql_names:
                if name!=sparql_name:
                    new_sparqldict[name]=self.sparqldict[name]
            with open(self.sds_path,"w+") as f:
                json.dump(new_sparqldict, f)


            st.session_state.sds_save_message = (
                f"SparQL Query {sparql_name} succesfully deleted!"
            )
            del st.session_state["sds_sel_del_ql_name"]
            del st.session_state["sds_show_query_name"]
            for mode in [self.sds_mode_dupl, self.sds_mode_edit]:
                if "sds_sel_query_name_" + mode in st.session_state:
                    del st.session_state["sds_sel_query_name_" + mode]
            st.session_state.sds_ace_key_counter+=1

        if len(self.editable_sparql_names) > 0:
            st.selectbox(
                label="Select a SparQL Query to delete!",
                options=self.editable_sparql_names,
                key="sds_sel_del_ql_name",
            )
            if self.validate_definition_for_delete(st.session_state.sds_sel_del_ql_name,self.sparqldict[st.session_state.sds_sel_del_ql_name]):
                st.button(
                    "Delete Selected SparQL Query",
                    on_click=delete_sds,
                    args=(st.session_state.sds_sel_del_ql_name,),
                )
        else:
            st.info("There are no self-defined ner task definitions to delete!")

    def show_edit_environment(self):
        sds_definer = st.expander("Add or edit existing SparQL Queries", expanded=False)
        with sds_definer:
            if self.sds_save_message is not None:
                st.success(self.sds_save_message)
            options = {
                "Add a SparQL Query": self.sparql_add,
                "Duplicate a SparQL Query": self.sparql_dupl,
                "Edit a SparQL Query": self.sparql_edit,
                "Delete a SparQL Query": self.sparql_del,
            }
            st.radio(label="Edit Options", options=tuple(options.keys()), index=0, key="sds_edit_option",on_change=self.reload_ace_components)
            options[st.session_state.sds_edit_option]()
            if self.sds_save_message is not None:
                st.success(self.sds_save_message)

    def build_sds_tablestring(self):
        tablestring = "Name |Template \n -----|-------"
        for sparqlname in self.sparqldict.keys():
            if sparqlname in self.editable_sparql_names:
                template = "no"
            else:
                template = "yes"
            tablestring += (
                "\n "
                + sparqlname
                + " | "
                + template
            )
        return tablestring

    def show_sds(self):
        sds_show = st.expander("Existing SparQLQuery Definitions", expanded=True)
        with sds_show:
            col1, col2= st.columns([0.3,0.7])
            with col1:
                st.markdown(self.build_sds_tablestring())
                st.markdown(" ")  # only for layouting reasons (placeholder)
            with col2:
                st.selectbox(label='Choose a SparQL Query for showing its details:',options=list(self.sparqldict.keys()),key='sds_show_query_name')
                st.subheader(f'Query to {st.session_state.sds_show_query_name}:')
                st.text(self.sparqldict[st.session_state.sds_show_query_name][0])
                st.subheader(f'Comment to {st.session_state.sds_show_query_name}:')
                st.text(self.sparqldict[st.session_state.sds_show_query_name][1])


    def show(self):
        st.latex("\\text{\Huge{SparQL Queries}}")
        self.show_sds()
        self.show_edit_environment()
