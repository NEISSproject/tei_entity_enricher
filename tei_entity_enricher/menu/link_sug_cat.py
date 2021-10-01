import streamlit as st
import json
import os
from tei_entity_enricher.util.helper import (
    local_save_path,
    makedir_if_necessary,
    menu_entity_definition,
    menu_link_sug_cat,
)
from tei_entity_enricher.interface.postprocessing.wikidata_connector import WikidataConnector
from streamlit_ace import st_ace

import tei_entity_enricher.menu.ner_task_def as ner_task


class LinkSugCat:
    def __init__(self, show_menu=True):
        self.lsc_Folder = os.path.join(local_save_path, "config", "postprocessing")
        self.lsc_mode_add = "add"
        self.lsc_mode_dupl = "duplicate"
        self.lsc_mode_edit = "edit"
        if "lsc_ace_key_counter" not in st.session_state:
            st.session_state.lsc_ace_key_counter = 0
        self.check_one_time_attributes()

        makedir_if_necessary(self.lsc_Folder)
        self.init_lsc_list()

        if show_menu:
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.show()

    def init_lsc_list(self):
        self.lsc_path = os.path.join(self.lsc_Folder, "link_sugesstion_categories.json")
        if not os.path.isfile(self.lsc_path):
            # Initialize Wikidata_Connector to build lsc templates:
            WikidataConnector()

        with open(self.lsc_path) as f:
            self.lscdict = json.load(f)
        self.editable_lsc_names = [
            lsc_name for lsc_name in self.lscdict if not self.lscdict[lsc_name][2]
        ]

    def check_one_time_attributes(self):
        if "lsc_save_message" in st.session_state and st.session_state.lsc_save_message is not None:
            self.lsc_save_message = st.session_state.lsc_save_message
            st.session_state.lsc_save_message = None
        else:
            self.lsc_save_message = None

    def validate_for_saving_lsc(self, name, content, mode):
        val = True
        if name is None or name == "":
            val = False
            st.error("Please define a name for the Link Suggestion Category before saving!")
        elif name in self.lscdict.keys() and mode != self.lsc_mode_edit:
            val = False
            st.error(f"Choose another name. There is already a Link Suggestion Category with name {name}!")
        return val

    def validate_definition_for_delete(self, name, content):
        val = True
        for definition in self.ntd.defslist:
            if self.ntd.ntd_attr_lsc_map in definition.keys():
                for entity in definition[self.ntd.ntd_attr_lsc_map].keys():
                    if definition[self.ntd.ntd_attr_lsc_map][entity] == name:
                        val = False
                        st.error(
                            f"Deletion of the Link Suggestion Category {name} is not allowed, because it is already used in the {menu_entity_definition} {definition[self.ntd.ntd_attr_name]}. If necessary first remove the assignment of the Link Suggestion Category from the {menu_entity_definition}."
                        )
        return val

    def reload_ace_components(self):
        st.session_state.lsc_ace_key_counter += 1

    def show_editable_lsc_content(self, mode):
        if mode == self.lsc_mode_edit and len(self.editable_lsc_names) < 1:
            st.info(
                f"There are no self-defined {menu_link_sug_cat} to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            if mode in [self.lsc_mode_dupl, self.lsc_mode_edit]:
                if self.lsc_mode_dupl == mode:
                    options = list(self.lscdict.keys())
                else:
                    options = self.editable_lsc_names
                st.selectbox(
                    f"Select a Link Suggestion Category to {mode}!",
                    options,
                    index=0,
                    key="lsc_sel_cat_name_" + mode,
                    on_change=self.reload_ace_components,
                )
                cur_query_content = self.lscdict[st.session_state["lsc_sel_cat_name_" + mode]].copy()
                cur_query_name = st.session_state["lsc_sel_cat_name_" + mode]
                if mode == self.lsc_mode_dupl:
                    cur_query_name = ""
            if mode == self.lsc_mode_add:
                cur_query_content = ["", ""]
            if mode in [self.lsc_mode_dupl, self.lsc_mode_add]:
                st.text_input(label="New Link Suggestion Category Name:", key="lsc_name_" + mode)
                cur_query_name = st.session_state["lsc_name_" + mode]
            st.markdown("Define the Link Suggestion Category:")
            query_content = st_ace(
                value=cur_query_content[0],
                height=200,
                language="sparql",
                readonly=False,
                key="lsc_ace_query_key" + str(st.session_state.lsc_ace_key_counter),
            )
            if query_content != cur_query_content[0]:
                cur_query_content[0] = query_content
            st.markdown("Comment:")
            comment_content = st_ace(
                value=cur_query_content[1],
                height=200,
                readonly=False,
                key="lsc_ace_comment_key" + str(st.session_state.lsc_ace_key_counter),
            )
            if comment_content != cur_query_content[1]:
                cur_query_content[1] = comment_content

            def save_lsc(cur_name, cur_content, mode):
                new_lscdict = {}
                for name in list(self.lscdict.keys()):
                    new_lscdict[name] = self.lscdict[name]
                new_lscdict[cur_name] = cur_content
                if len(new_lscdict[cur_name]) < 3:
                    new_lscdict[cur_name].append(False)
                else:
                    new_lscdict[cur_name][2] = False
                with open(self.lsc_path, "w+") as f:
                    json.dump(new_lscdict, f, indent=4)

                st.session_state.lsc_save_message = f"Link Suggestion Category {cur_name} succesfully saved!"
                if mode != self.lsc_mode_edit:
                    st.session_state["lsc_name_" + mode] = ""
                # del st.session_state["lsc_show_query_name"]
                st.session_state.lsc_ace_key_counter += 1

            if self.validate_for_saving_lsc(cur_query_name, cur_query_content, mode):
                st.button(
                    "Save Link Suggestion Category",
                    on_click=save_lsc,
                    args=(
                        cur_query_name,
                        cur_query_content,
                        mode,
                    ),
                )

    def lsc_add(self):
        self.show_editable_lsc_content(self.lsc_mode_add)

    def lsc_dupl(self):
        self.show_editable_lsc_content(self.lsc_mode_dupl)

    def lsc_edit(self):
        self.show_editable_lsc_content(self.lsc_mode_edit)

    def lsc_del(self):
        def delete_lsc(lsc_name):
            new_lscdict = {}
            for name in list(self.lscdict.keys()):
                if name != lsc_name:
                    new_lscdict[name] = self.lscdict[name]
            with open(self.lsc_path, "w+") as f:
                json.dump(new_lscdict, f, indent=4)

            st.session_state.lsc_save_message = f"Link Suggestion Category {lsc_name} succesfully deleted!"
            del st.session_state["lsc_sel_del_ql_name"]
            del st.session_state["lsc_show_query_name"]
            for mode in [self.lsc_mode_dupl, self.lsc_mode_edit]:
                if "lsc_sel_cat_name_" + mode in st.session_state:
                    del st.session_state["lsc_sel_cat_name_" + mode]
            st.session_state.lsc_ace_key_counter += 1

        if len(self.editable_lsc_names) > 0:
            st.selectbox(
                label="Select a Link Suggestion Category to delete!",
                options=self.editable_lsc_names,
                key="lsc_sel_del_ql_name",
            )
            if self.validate_definition_for_delete(
                st.session_state.lsc_sel_del_ql_name, self.lscdict[st.session_state.lsc_sel_del_ql_name]
            ):
                st.button(
                    "Delete Selected Link Suggestion Category",
                    on_click=delete_lsc,
                    args=(st.session_state.lsc_sel_del_ql_name,),
                )
        else:
            st.info(f"There are no self-defined {menu_link_sug_cat} to delete!")

    def show_edit_environment(self):
        lsc_definer = st.expander(f"Add or edit existing {menu_link_sug_cat}", expanded=False)
        with lsc_definer:
            if self.lsc_save_message is not None:
                st.success(self.lsc_save_message)
            options = {
                "Add a Link Suggestion Category": self.lsc_add,
                "Duplicate a Link Suggestion Category": self.lsc_dupl,
                "Edit a Link Suggestion Category": self.lsc_edit,
                "Delete a Link Suggestion Category": self.lsc_del,
            }
            st.radio(
                label="Edit Options",
                options=tuple(options.keys()),
                index=0,
                key="lsc_edit_option",
                on_change=self.reload_ace_components,
            )
            options[st.session_state.lsc_edit_option]()
            if self.lsc_save_message is not None:
                st.success(self.lsc_save_message)

    def build_lsc_tablestring(self):
        tablestring = "Name |Template \n -----|-------"
        for lscname in self.lscdict.keys():
            if lscname in self.editable_lsc_names:
                template = "no"
            else:
                template = "yes"
            tablestring += "\n " + lscname + " | " + template
        return tablestring

    def show_lsc(self):
        lsc_show = st.expander("Existing Link Suggestion Category Definitions", expanded=True)
        with lsc_show:
            col1, col2 = st.columns([0.3, 0.7])
            with col1:
                st.markdown(self.build_lsc_tablestring())
                st.markdown(" ")  # only for layouting reasons (placeholder)
            with col2:
                st.selectbox(
                    label="Choose a Link Suggestion Category for showing its details:",
                    options=list(self.lscdict.keys()),
                    key="lsc_show_query_name",
                )
                st.subheader(f"Query to {st.session_state.lsc_show_query_name}:")
                st.text(self.lscdict[st.session_state.lsc_show_query_name][0])
                st.subheader(f"Comment to {st.session_state.lsc_show_query_name}:")
                st.text(self.lscdict[st.session_state.lsc_show_query_name][1])

    def show(self):
        st.latex("\\text{\Huge{" + menu_link_sug_cat + "}}")
        self.show_lsc()
        self.show_edit_environment()
