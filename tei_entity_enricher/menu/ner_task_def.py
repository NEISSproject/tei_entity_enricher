import streamlit as st
import json
import os
from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
    menu_entity_definition,
    menu_TEI_read_mapping,
    menu_TEI_write_mapping,
)
from tei_entity_enricher.util.components import (
    editable_single_column_table,
)
import tei_entity_enricher.menu.tei_ner_map as tei_map
import tei_entity_enricher.menu.tei_ner_writer_map as tei_w_map
import tei_entity_enricher.menu.link_sug_cat as ls_cat

withoutLSC = "without default Link Suggestion Category"


class NERTaskDef:
    def __init__(self, show_menu=True):
        self.ntd_Folder = "NTD"
        self.template_ntd_Folder = os.path.join(module_path, "templates", self.ntd_Folder)
        self.ntd_Folder = os.path.join(local_save_path, self.ntd_Folder)
        self.ntd_attr_name = "name"
        self.ntd_attr_entitylist = "entitylist"
        self.ntd_attr_template = "template"
        self.ntd_attr_lsc_map = "ls_cat"
        self.ntd_mode_add = "add"
        self.ntd_mode_dupl = "duplicate"
        self.ntd_mode_edit = "edit"
        self.check_one_time_attributes()

        makedir_if_necessary(self.ntd_Folder)
        makedir_if_necessary(self.template_ntd_Folder)

        self.defslist = []
        for defFile in sorted(os.listdir(self.template_ntd_Folder)):
            if defFile.endswith("json"):
                with open(os.path.join(self.template_ntd_Folder, defFile)) as f:
                    self.defslist.append(json.load(f))
        for defFile in sorted(os.listdir(self.ntd_Folder)):
            if defFile.endswith("json"):
                with open(os.path.join(self.ntd_Folder, defFile)) as f:
                    self.defslist.append(json.load(f))

        self.defdict = {}
        self.editable_def_names = []
        for definition in self.defslist:
            self.defdict[definition[self.ntd_attr_name]] = definition
            if not definition[self.ntd_attr_template]:
                self.editable_def_names.append(definition[self.ntd_attr_name])

        if show_menu:
            self.tnm = tei_map.TEINERMap(show_menu=False)
            self.tnw = tei_w_map.TEINERPredWriteMap(show_menu=False)
            self.lsc = ls_cat.LinkSugCat(show_menu=False)
            self.show()

    def check_one_time_attributes(self):
        if "ntd_save_message" in st.session_state and st.session_state.ntd_save_message is not None:
            self.ntd_save_message = st.session_state.ntd_save_message
            st.session_state.ntd_save_message = None
        else:
            self.ntd_save_message = None

        if "ntd_reload_aggrids" in st.session_state and st.session_state.ntd_reload_aggrids == True:
            self.ntd_reload_aggrids = True
            st.session_state.ntd_reload_aggrids = False
        else:
            self.ntd_reload_aggrids = False

    def get_tag_filepath_to_ntdname(self, name):
        if self.defdict[name][self.ntd_attr_template]:
            ntd_tag_file = os.path.join(self.template_ntd_Folder, name.replace(" ", "_") + ".txt")
        else:
            ntd_tag_file = os.path.join(self.ntd_Folder, name.replace(" ", "_") + ".txt")
        return ntd_tag_file

    def validate_for_saving_definition(self, definition, mode):
        val = True
        if (
            self.ntd_attr_name not in definition.keys()
            or definition[self.ntd_attr_name] is None
            or definition[self.ntd_attr_name] == ""
        ):
            val = False
            if self.ntd_save_message is None:
                st.error(f"Please define a name for the {menu_entity_definition} before saving!")
        elif (
            os.path.isfile(
                os.path.join(
                    self.ntd_Folder,
                    definition[self.ntd_attr_name].replace(" ", "_") + ".json",
                )
            )
            and mode != self.ntd_mode_edit
        ):
            val = False
            if self.ntd_save_message is None:
                st.error(
                    f"Choose another name. There is already an {menu_entity_definition} with name {definition[self.ntd_attr_name]}!"
                )

        if self.ntd_attr_entitylist not in definition.keys() or len(definition[self.ntd_attr_entitylist]) == 0:
            val = False
            if self.ntd_save_message is None:
                st.error(f"Please define at least one entity for the {menu_entity_definition}!")
        else:
            if len(definition[self.ntd_attr_entitylist]) != len(set(definition[self.ntd_attr_entitylist])):
                val = False
                if self.ntd_save_message is None:
                    st.error("There are at least two entities with the same name. This is not allowed!")
            for entity in definition[self.ntd_attr_entitylist]:
                if " " in entity:
                    val = False
                    if self.ntd_save_message is None:
                        st.error(
                            f"You defined an entity name ({entity}) containing a space character. This is not allowed!"
                        )
        for mapping in self.tnm.mappingslist:
            if mapping[self.tnm.tnm_attr_ntd][self.ntd_attr_name] == definition[self.ntd_attr_name]:
                val = False
                if self.ntd_save_message is None:
                    st.error(
                        f"To edit the {menu_entity_definition} {definition[self.ntd_attr_name]} is not allowed because it is already used in the {menu_TEI_read_mapping} {mapping[self.tnm.tnm_attr_name]}. If necessary, first remove the assignment of the {menu_entity_definition} to the mapping."
                    )
        for mapping in self.tnw.mappingslist:
            if mapping[self.tnw.tnw_attr_ntd][self.ntd_attr_name] == definition[self.ntd_attr_name]:
                val = False
                if self.ntd_save_message is None:
                    st.error(
                        f"To edit the {menu_entity_definition} {definition[self.ntd_attr_name]} is not allowed because it is already used in the {menu_TEI_write_mapping} {mapping[self.tnw.tnw_attr_name]}. If necessary, first remove the assignment of the {menu_entity_definition} to the mapping."
                    )
        return val

    def validate_definition_for_delete(self, definition):
        val = True
        for mapping in self.tnm.mappingslist:
            if mapping[self.tnm.tnm_attr_ntd][self.ntd_attr_name] == definition[self.ntd_attr_name]:
                val = False
                if self.ntd_save_message is None:
                    st.error(
                        f"Deletion of the {menu_entity_definition} {definition[self.ntd_attr_name]} not allowed because it is already used in the {menu_TEI_read_mapping} {mapping[self.tnm.tnm_attr_name]}. If necessary, first remove the assignment of the {menu_entity_definition} to the mapping."
                    )
        for mapping in self.tnw.mappingslist:
            if mapping[self.tnw.tnw_attr_ntd][self.ntd_attr_name] == definition[self.ntd_attr_name]:
                val = False
                if self.ntd_save_message is None:
                    st.error(
                        f"Deletion of the {menu_entity_definition} {definition[self.ntd_attr_name]} not allowed because it is already used in the {menu_TEI_write_mapping} {mapping[self.tnw.tnw_attr_name]}. If necessary, first remove the assignment of the {menu_entity_definition} to the mapping."
                    )
        return val

    def show_editable_entitylist(self, entitylist, key):
        st.markdown(f"Define a list of entities for the {menu_entity_definition}.")
        return editable_single_column_table(
            entry_list=entitylist, key=key, head="Entities", reload=self.ntd_reload_aggrids
        )

    def build_entitylist_key(self, mode):
        return (
            "ntd_entitylist_"
            + mode
            + ("" if mode == self.ntd_mode_add else st.session_state["ntd_sel_def_name_" + mode])
        )

    def show_editable_definition_content(self, mode):
        if mode == self.ntd_mode_edit and len(self.editable_def_names) < 1:
            st.info(
                f"There are no self-defined {menu_entity_definition}s to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            ntd_definition_dict = {}
            if mode in [self.ntd_mode_dupl, self.ntd_mode_edit]:
                if self.ntd_mode_dupl == mode:
                    options = list(self.defdict.keys())
                else:
                    options = self.editable_def_names

                def change_ntd_sel_def_name():
                    st.session_state.ntd_init_lsc_map = True

                st.selectbox(
                    f"Select a definition to {mode}!",
                    options,
                    index=0,
                    key="ntd_sel_def_name_" + mode,
                    on_change=change_ntd_sel_def_name,
                )
                ntd_definition_dict = self.defdict[st.session_state["ntd_sel_def_name_" + mode]].copy()
                if mode == self.ntd_mode_dupl:
                    ntd_definition_dict[self.ntd_attr_name] = ""
            if mode == self.ntd_mode_add:
                ntd_definition_dict[self.ntd_attr_entitylist] = []
            if mode in [self.ntd_mode_dupl, self.ntd_mode_add]:
                st.text_input(label=f"New {menu_entity_definition} Name:", key="ntd_name_" + mode)
                ntd_definition_dict[self.ntd_attr_name] = st.session_state["ntd_name_" + mode]
            init_entitylist = ntd_definition_dict[self.ntd_attr_entitylist]
            ntd_definition_dict[self.ntd_attr_entitylist] = self.show_editable_entitylist(
                entitylist=init_entitylist,
                key=self.build_entitylist_key(mode),
            )
            if len(ntd_definition_dict[self.ntd_attr_entitylist]) > 0:
                st.markdown("Define a default Link Suggestion Category for a chosen Entity:")
                if not self.ntd_attr_lsc_map in ntd_definition_dict.keys():
                    ntd_definition_dict[self.ntd_attr_lsc_map] = {}
                if "ntd_lsc_map" not in st.session_state:
                    st.session_state.ntd_lsc_map = {}
                if "ntd_init_lsc_map" not in st.session_state or st.session_state.ntd_init_lsc_map:
                    st.session_state.ntd_lsc_map = ntd_definition_dict[self.ntd_attr_lsc_map]
                    st.session_state.ntd_init_lsc_map = False
                else:
                    ntd_definition_dict[self.ntd_attr_lsc_map] = st.session_state.ntd_lsc_map
                lsc_entity = st.selectbox(
                    label="Choose an Entity:", options=ntd_definition_dict[self.ntd_attr_entitylist]
                )
                lscoptions = [withoutLSC]
                lscoptions.extend(list(self.lsc.lscdict.keys()))
                init_query_index = (
                    lscoptions.index(st.session_state.ntd_lsc_map[lsc_entity])
                    if lsc_entity in st.session_state.ntd_lsc_map.keys()
                    else 0
                )
                lsc_query = st.selectbox(
                    label=f"Choose a default lsc Query for the Entity {lsc_entity}.",
                    options=lscoptions,
                    index=init_query_index,
                )
                st.session_state.ntd_lsc_map[lsc_entity] = lsc_query
                if st.session_state.ntd_lsc_map[lsc_entity] != withoutLSC:
                    ntd_definition_dict[self.ntd_attr_lsc_map][lsc_entity] = lsc_query
                elif lsc_entity in st.session_state.ntd_lsc_map.keys():
                    del ntd_definition_dict[self.ntd_attr_lsc_map][lsc_entity]
            # ntd_definition_dict[self.ntd_attr_entitylist] = self.get_editable_entitylist(self.build_entitylist_key(mode))
            def save_ntd(definition, mode):
                definition[self.ntd_attr_template] = False
                with open(
                    os.path.join(
                        self.ntd_Folder,
                        definition[self.ntd_attr_name].replace(" ", "_") + ".json",
                    ),
                    "w+",
                ) as f:
                    json.dump(definition, f)
                blines = []
                ilines = []
                for entity in definition[self.ntd_attr_entitylist]:
                    blines.append("B-" + entity + "\n")
                    ilines.append("I-" + entity + "\n")
                blines.extend(ilines)
                with open(
                    os.path.join(
                        self.ntd_Folder,
                        definition[self.ntd_attr_name].replace(" ", "_") + ".txt",
                    ),
                    "w+",
                ) as f:
                    f.writelines(blines)
                st.session_state.ntd_save_message = (
                    f"{menu_entity_definition} {definition[self.ntd_attr_name]} succesfully saved!"
                )
                st.session_state.ntd_reload_aggrids = True
                if mode != self.ntd_mode_edit:
                    st.session_state["ntd_name_" + mode] = ""
                for key in st.session_state:
                    if key.startswith("ntd_entitylist_" + mode):
                        del st.session_state[key]

            if self.validate_for_saving_definition(ntd_definition_dict, mode):
                st.button(
                    f"Save {menu_entity_definition}",
                    on_click=save_ntd,
                    args=(
                        ntd_definition_dict,
                        mode,
                    ),
                )

    def tei_ner_map_add(self):
        self.show_editable_definition_content(self.ntd_mode_add)

    def tei_ner_map_dupl(self):
        self.show_editable_definition_content(self.ntd_mode_dupl)

    def tei_ner_map_edit(self):
        self.show_editable_definition_content(self.ntd_mode_edit)

    def tei_ner_map_del(self):
        def delete_ntd(definition):
            os.remove(
                os.path.join(
                    self.ntd_Folder,
                    definition[self.ntd_attr_name].replace(" ", "_") + ".json",
                )
            )
            os.remove(
                os.path.join(
                    self.ntd_Folder,
                    definition[self.ntd_attr_name].replace(" ", "_") + ".txt",
                )
            )
            st.session_state.ntd_save_message = (
                f"{menu_entity_definition} {definition[self.ntd_attr_name]} succesfully deleted!"
            )
            st.session_state.ntd_reload_aggrids = True
            del st.session_state["ntd_sel_del_def_name"]
            for mode in [self.ntd_mode_dupl, self.ntd_mode_edit]:
                if "ntd_sel_def_name_" + mode in st.session_state:
                    del st.session_state["ntd_sel_def_name_" + mode]

        if len(self.editable_def_names) > 0:
            st.selectbox(
                label=f"Select a {menu_entity_definition} to delete!",
                options=self.editable_def_names,
                index=0,
                key="ntd_sel_del_def_name",
            )
            if self.validate_definition_for_delete(self.defdict[st.session_state.ntd_sel_del_def_name]):
                st.button(
                    f"Delete Selected {menu_entity_definition}",
                    on_click=delete_ntd,
                    args=(self.defdict[st.session_state.ntd_sel_del_def_name],),
                )
        else:
            st.info(f"There are no self-defined {menu_entity_definition}s to delete!")

    def show_edit_environment(self):
        ntd_definer = st.expander(f"Add or edit existing {menu_entity_definition}", expanded=False)
        with ntd_definer:
            if self.ntd_save_message is not None:
                st.success(self.ntd_save_message)
            options = {
                f"Add {menu_entity_definition}": self.tei_ner_map_add,
                f"Duplicate {menu_entity_definition}": self.tei_ner_map_dupl,
                f"Edit {menu_entity_definition}": self.tei_ner_map_edit,
                f"Delete {menu_entity_definition}": self.tei_ner_map_del,
            }

            def change_edit_option():
                st.session_state.ntd_init_lsc_map = True

            st.radio(
                label="Edit Options",
                options=tuple(options.keys()),
                index=0,
                key="ntd_edit_option",
                on_change=change_edit_option,
            )
            options[st.session_state.ntd_edit_option]()
            if self.ntd_save_message is not None:
                st.success(self.ntd_save_message)

    def build_ntd_tablestring(self):
        tablestring = "Name | Entities | Link Suggestion Category | Template \n -----|-------|-------|-------"
        for definition in self.defslist:
            if definition[self.ntd_attr_template]:
                template = "yes"
            else:
                template = "no"
            lsc = ""
            entitystring = ""
            for entity in definition[self.ntd_attr_entitylist]:
                if entitystring != "":
                    entitystring += " <br> "
                    lsc += " <br> "
                entitystring += entity
                if self.ntd_attr_lsc_map in definition.keys() and entity in definition[self.ntd_attr_lsc_map].keys():
                    lsc += definition[self.ntd_attr_lsc_map][entity]
                else:
                    lsc += "-"

            tablestring += (
                "\n " + definition[self.ntd_attr_name] + " | " + entitystring + " | " + lsc + " | " + template
            )
        return tablestring

    def show_ntds(self):
        ntd_show = st.expander(f"Existing {menu_entity_definition}s", expanded=True)
        with ntd_show:
            st.markdown(
                self.build_ntd_tablestring(),
                unsafe_allow_html=True,
            )
            st.markdown(" ")  # only for layouting reasons (placeholder)

    def show(self):
        st.latex("\\text{\Huge{" + menu_entity_definition + "}}")
        col1, col2 = st.columns(2)
        with col1:
            self.show_ntds()
        with col2:
            self.show_edit_environment()
