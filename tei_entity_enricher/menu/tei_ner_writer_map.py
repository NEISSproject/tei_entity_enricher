import streamlit as st
import json
import os

from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
    get_listoutput,
)
from tei_entity_enricher.util.components import editable_multi_column_table, editable_single_column_table
import tei_entity_enricher.menu.ner_task_def as ner_task


class TEINERPredWriteMap:
    def __init__(self, state, show_menu=True):
        self.state = state

        self.tnw_Folder = "TNW"
        self.template_tnw_Folder = os.path.join(module_path, "templates", self.tnw_Folder)
        self.tnw_Folder = os.path.join(local_save_path, self.tnw_Folder)
        self.tnw_attr_name = "name"
        self.tnw_attr_ntd = "ntd"
        self.tnw_attr_template = "template"
        self.tnw_attr_entity_dict = "entity_dict"
        self.tnw_attr_fixed_tags = "fixed_tags"
        self.tnw_mode_add = "add"
        self.tnw_mode_dupl = "duplicate"
        self.tnw_mode_edit = "edit"

        makedir_if_necessary(self.tnw_Folder)
        makedir_if_necessary(self.template_tnw_Folder)

        self.mappingslist = []
        for mappingFile in sorted(os.listdir(self.template_tnw_Folder)):
            if mappingFile.endswith("json"):
                with open(os.path.join(self.template_tnw_Folder, mappingFile)) as f:
                    self.mappingslist.append(json.load(f))
        for mappingFile in sorted(os.listdir(self.tnw_Folder)):
            if mappingFile.endswith("json"):
                with open(os.path.join(self.tnw_Folder, mappingFile)) as f:
                    self.mappingslist.append(json.load(f))

        self.mappingdict = {}
        self.editable_mapping_names = []
        for mapping in self.mappingslist:
            self.mappingdict[mapping[self.tnw_attr_name]] = mapping
            if not mapping[self.tnw_attr_template]:
                self.editable_mapping_names.append(mapping[self.tnw_attr_name])

        if show_menu:
            self.ntd = ner_task.NERTaskDef(state, show_menu=False)
            self.show()

    def validate_and_saving_mapping(self, mapping, mode):
        val = True
        if (
            self.tnw_attr_name not in mapping.keys()
            or mapping[self.tnw_attr_name] is None
            or mapping[self.tnw_attr_name] == ""
        ):
            val = False
            st.error("Please define a name for the mapping before saving!")
        elif (
            os.path.isfile(
                os.path.join(
                    self.tnw_Folder,
                    mapping[self.tnw_attr_name].replace(" ", "_") + ".json",
                )
            )
            and mode != self.tnw_mode_edit
        ):
            val = False
            st.error(f"Choose another name. There is already a mapping with name {mapping[self.tnw_attr_name]}!")
        if len(mapping[self.tnw_attr_fixed_tags]) > 0:
            for fix_tag in mapping[self.tnw_attr_fixed_tags]:
                if " " in fix_tag:
                    val = False
                    st.error(
                        f"You defined an fixed tag ({fix_tag}) containing a space character. This is not allowed!"
                    )
        # clear empty mapping entries
        entities_to_del = []
        for entity in mapping[self.tnw_attr_entity_dict].keys():
            del_entity = True
            if (
                mapping[self.tnw_attr_entity_dict][entity][0] is not None
                and mapping[self.tnw_attr_entity_dict][entity][0] != ""
            ):
                if " " in mapping[self.tnw_attr_entity_dict][entity][0]:
                    val = False
                    st.error(
                        f"For the entity {entity} you defined the tag name ({mapping[self.tnw_attr_entity_dict][entity][0]}) containing a space character. This is not allowed!"
                    )
                for attribute in mapping[self.tnw_attr_entity_dict][entity][1].keys():
                    if (
                        (attribute is None or attribute == "")
                        and mapping[self.tnw_attr_entity_dict][entity][1][attribute] is not None
                        and mapping[self.tnw_attr_entity_dict][entity][1][attribute] != ""
                    ):
                        val = False
                        st.error(
                            f"For the entity {entity} and tag {mapping[self.tnw_attr_entity_dict][entity][0]} you defined an attribute value {mapping[self.tnw_attr_entity_dict][entity][1][attribute]} without a corresponding attribute name. This is not allowed."
                        )
                    elif (
                        attribute is not None and attribute != ""
                        and (mapping[self.tnw_attr_entity_dict][entity][1][attribute] is None
                        or mapping[self.tnw_attr_entity_dict][entity][1][attribute] == "")
                    ):
                        val = False
                        st.error(
                            f"For the entity {entity} and tag {mapping[self.tnw_attr_entity_dict][entity][0]} you defined the attribute {attribute} without a value for it. This is not allowed."
                        )
                    elif " " in attribute:
                        val = False
                        st.error(
                            f"For the entity {entity} and tag {mapping[self.tnw_attr_entity_dict][entity][0]} you defined an attribute name ({attribute}) containing a space character. This is not allowed!"
                        )
                    elif " " in mapping[self.tnw_attr_entity_dict][entity][1][attribute]:
                        val = False
                        st.error(
                            f"For the entity {entity} and tag {mapping[self.tnw_attr_entity_dict][entity][0]} you defined for the attribute {attribute} a value ({mapping[self.tnw_attr_entity_dict][entity][1][attribute]}) containing a space character. This is not allowed!"
                        )
                del_entity = False
            if del_entity:
                entities_to_del.append(entity)
        for entity in entities_to_del:
            del mapping[self.tnw_attr_entity_dict][entity]

        if len(mapping[self.tnw_attr_entity_dict].keys()) == 0:
            val = False
            st.error(f"Please define at least one mapping of an entity to a tag. Otherwise there is nothing to save.")

        if val:
            mapping[self.tnw_attr_template] = False
            with open(
                os.path.join(
                    self.tnw_Folder,
                    mapping[self.tnw_attr_name].replace(" ", "_") + ".json",
                ),
                "w+",
            ) as f:
                json.dump(mapping, f)
            self.reset_tnw_edit_states()
            st.experimental_rerun()

    def validate_and_delete_mapping(self, mapping):
        val = True
        if val:
            os.remove(
                os.path.join(
                    self.tnw_Folder,
                    mapping[self.tnw_attr_name].replace(" ", "_") + ".json",
                )
            )
            self.reset_tnw_edit_states()
            self.state.tnw_sel_mapping_name = None
            st.experimental_rerun()

    def reset_tnw_edit_states(self):
        self.state.tnw_name = None
        self.state.tnw_ntd_name = None
        self.state.tnw_entity_dict = None

    def show_editable_fixed_tags(self, fixed_list, mode, name):
        st.markdown("Define tags in which no entities should be written.")
        return editable_single_column_table(entry_list=fixed_list, key="tnw_fixed" + mode + name, head="Fixed Tags")

    def show_editable_attr_value_def(self, attr_value_dict, name):
        st.markdown("Define optionally attributes with values which have to be set for this tag!")
        entry_dict = {"Attributes": [], "Values": []}
        for key in attr_value_dict.keys():
            entry_dict["Attributes"].append(key)
            entry_dict["Values"].append(attr_value_dict[key])
        answer = editable_multi_column_table(entry_dict, "tnw_attr_value" + name, openentrys=20)
        returndict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in returndict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            returndict[answer["Attributes"][i]] = answer["Values"][i]
        return returndict

    def show_editable_mapping_content(self, mode):
        if mode == self.tnw_mode_edit and len(self.editable_mapping_names) < 1:
            st.info(
                "There are no self-defined TEI NER Prediction Writer Mappings to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            if self.state.tnw_mode != mode:
                self.reset_tnw_edit_states()
            self.state.tnw_mode = mode
            tnw_mapping_dict = {}
            init_tnw_ntd_name = self.state.tnw_ntd_name
            init_tnw_entity_dict = {}
            if mode in [self.tnw_mode_dupl, self.tnw_mode_edit]:
                if self.tnw_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                selected_tnw_name = st.selectbox(f"Select a mapping to {mode}!", options, key="tnw" + mode)
                if self.state.tnw_sel_mapping_name != selected_tnw_name:
                    self.reset_tnw_edit_states()
                self.state.tnw_sel_mapping_name = selected_tnw_name
                tnw_mapping_dict = self.mappingdict[selected_tnw_name].copy()
                init_tnw_ntd_name = tnw_mapping_dict[self.tnw_attr_ntd][self.ntd.ntd_attr_name]
                init_tnw_entity_dict = tnw_mapping_dict[self.tnw_attr_entity_dict]
                if mode == self.tnw_mode_dupl:
                    tnw_mapping_dict[self.tnw_attr_name] = ""
            if mode == self.tnw_mode_add:
                tnw_mapping_dict[self.tnw_attr_ntd] = {}
                tnw_mapping_dict[self.tnw_attr_entity_dict] = {}
                tnw_mapping_dict[self.tnw_attr_fixed_tags] = []
            if mode in [self.tnw_mode_dupl, self.tnw_mode_add]:
                self.state.tnw_name = st.text_input(
                    "New TEI NER Prediction Writer Mapping Name:", self.state.tnw_name or ""
                )
                if self.state.tnw_name:
                    tnw_mapping_dict[self.tnw_attr_name] = self.state.tnw_name
            sel_tnw_ntd_name = st.selectbox(
                "Corresponding NER task definition",
                list(self.ntd.defdict.keys()),
                list(self.ntd.defdict.keys()).index(init_tnw_ntd_name) if init_tnw_ntd_name else 0,
                key="tnw_ntd_sel" + mode,
            )
            init_fixed_list = tnw_mapping_dict[self.tnw_attr_fixed_tags]
            self.state.tnw_fixed_list = self.show_editable_fixed_tags(
                self.state.tnw_fixed_list if self.state.tnw_fixed_list else init_fixed_list,
                mode,
                tnw_mapping_dict[self.tnw_attr_name] if self.tnw_attr_name in tnw_mapping_dict.keys() else "",
            )
            if self.state.tnw_ntd_name and sel_tnw_ntd_name != self.state.tnw_ntd_name:
                self.state.tnw_entity_dict = None
            self.state.tnw_ntd_name = sel_tnw_ntd_name
            if self.state.tnw_ntd_name:
                tnw_edit_entity = st.selectbox(
                    "Define mapping for entity:",
                    self.ntd.defdict[self.state.tnw_ntd_name][self.ntd.ntd_attr_entitylist],
                    key="tnw_ent" + mode,
                )
                if tnw_edit_entity:
                    self.state.tnw_entity_dict = self.edit_entity(
                        mode,
                        tnw_edit_entity,
                        self.state.tnw_entity_dict if self.state.tnw_entity_dict else init_tnw_entity_dict,
                    )

            if st.button("Save TEI NER Prediction Writer Mapping", key=mode):
                tnw_mapping_dict[self.tnw_attr_ntd] = self.ntd.defdict[self.state.tnw_ntd_name]
                tnw_mapping_dict[self.tnw_attr_fixed_tags] = self.state.tnw_fixed_list
                tnw_mapping_dict[self.tnw_attr_entity_dict] = self.state.tnw_entity_dict.copy()
                self.validate_and_saving_mapping(tnw_mapping_dict, mode)

    def edit_entity(self, mode, tnw_edit_entity, cur_entity_dict):
        if tnw_edit_entity not in cur_entity_dict.keys():
            cur_entity_dict[tnw_edit_entity] = [None, {}]
        mapping_entry = cur_entity_dict[tnw_edit_entity]
        mapping_entry[0] = st.text_input(
            "Tag",
            mapping_entry[0] or "",
            key="tnw" + self.state.tnw_ntd_name + tnw_edit_entity + mode,
        )
        if mapping_entry[0]:
            mapping_entry[1] = self.show_editable_attr_value_def(mapping_entry[1], tnw_edit_entity + mode)
        return cur_entity_dict

    def tei_ner_map_add(self):
        self.show_editable_mapping_content(self.tnw_mode_add)

    def tei_ner_map_dupl(self):
        self.show_editable_mapping_content(self.tnw_mode_dupl)

    def tei_ner_map_edit(self):
        self.show_editable_mapping_content(self.tnw_mode_edit)

    def tei_ner_map_del(self):
        selected_mapping_name = st.selectbox("Select a mapping to delete!", self.editable_mapping_names)
        if st.button("Delete Selected Mapping"):
            self.validate_and_delete_mapping(self.mappingdict[selected_mapping_name])

    def show_edit_environment(self):
        tnw_definer = st.beta_expander("Add or edit existing TEI NER Prediction Writer Mapping", expanded=False)
        with tnw_definer:
            options = {
                "Add TEI NER Prediction Writer Mapping": self.tei_ner_map_add,
                "Duplicate TEI NER Prediction Writer Mapping": self.tei_ner_map_dupl,
                "Edit TEI NER Prediction Writer Mapping": self.tei_ner_map_edit,
                "Delete TEI NER Prediction Writer Mapping": self.tei_ner_map_del,
            }
            self.state.tnw_edit_options = st.radio(
                "Edit Options",
                tuple(options.keys()),
                tuple(options.keys()).index(self.state.tnw_edit_options) if self.state.tnw_edit_options else 0,
            )
            options[self.state.tnw_edit_options]()

    def build_tnw_tablestring(self):
        tablestring = "Name | NER Task | Fixed Tags | Template \n -----|-------|-------|-------"
        for mapping in self.mappingslist:
            if mapping[self.tnw_attr_template]:
                template = "yes"
            else:
                template = "no"
            tablestring += (
                "\n "
                + mapping[self.tnw_attr_name]
                + " | "
                + mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_name]
                + " | "
                + get_listoutput(mapping[self.tnw_attr_fixed_tags])
                + " | "
                + template
            )
        return tablestring

    def build_tnw_entity_detail_string(self, entity_detail):
        tag_string = ""
        attr_string = ""
        cur_len = len(entity_detail[1].keys())
        tag_string += entity_detail[0]
        if cur_len == 0:
            attr_string += " "
        else:
            for attr in entity_detail[1].keys():
                attr_string += attr + "=" + entity_detail[1][attr] + ","
            attr_string = attr_string[:-1]
        return tag_string + " | " + attr_string

    def build_tnw_detail_tablestring(self, tnw):
        tablestring = "Entity | Tag | Attributes \n -----|-------|-------"
        for entity in tnw[self.tnw_attr_entity_dict].keys():
            tablestring += (
                "\n " + entity + " | " + self.build_tnw_entity_detail_string(tnw[self.tnw_attr_entity_dict][entity])
            )
        return tablestring

    def show_tnws(self):
        tnw_show = st.beta_expander("Existing TEI NER Prediction Writer Mappings", expanded=True)
        with tnw_show:
            st.markdown(self.build_tnw_tablestring())
            self.state.tnw_selected_display_tnw_name = st.selectbox(
                f"Choose a mapping for displaying its details:",
                list(self.mappingdict.keys()),
                key="tnw_details",
            )
            if self.state.tnw_selected_display_tnw_name:
                cur_sel_mapping = self.mappingdict[self.state.tnw_selected_display_tnw_name]
                st.markdown(
                    self.build_tnw_detail_tablestring(cur_sel_mapping),
                    unsafe_allow_html=True,
                )
                if len(cur_sel_mapping[self.tnw_attr_entity_dict].keys()) < len(
                    cur_sel_mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]
                ):
                    st.warning(
                        f"Warning: The Mapping {cur_sel_mapping[self.tnw_attr_name]} is possibly incomplete. Not every entity of the corresponding task {cur_sel_mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_name]} is assigned a tag."
                    )

    def show(self):
        st.latex("\\text{\Huge{TEI NER Prediction Writer Mapping}}")
        col1, col2 = st.beta_columns(2)
        with col1:
            self.show_tnws()
        with col2:
            self.show_edit_environment()
