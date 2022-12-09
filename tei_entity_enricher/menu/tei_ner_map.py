import streamlit as st
import json
import os

from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
    transform_arbitrary_text_to_latex,
    latex_color_list,
    menu_entity_definition,
    menu_TEI_reader_config,
    menu_TEI_read_mapping,
    is_accepted_TEI_filename,
)
from tei_entity_enricher.util.components import (
    editable_multi_column_table,
    small_file_selector,
)
import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_gb as gb
import tei_entity_enricher.util.tei_parser as tp


class TEINERMap:
    def __init__(self, show_menu=True):
        self.tnm_Folder = "TNM"
        self.template_tnm_Folder = os.path.join(module_path, "templates", self.tnm_Folder)
        self.tnm_Folder = os.path.join(local_save_path, self.tnm_Folder)
        self.tnm_attr_name = "name"
        self.tnm_attr_ntd = "ntd"
        self.tnm_attr_template = "template"
        self.tnm_attr_entity_dict = "entity_dict"
        self.tnm_mode_add = "add"
        self.tnm_mode_dupl = "duplicate"
        self.tnm_mode_edit = "edit"
        self.check_one_time_attributes()

        makedir_if_necessary(self.tnm_Folder)
        makedir_if_necessary(self.template_tnm_Folder)

        self.mappingslist = []
        for mappingFile in sorted(os.listdir(self.template_tnm_Folder)):
            if mappingFile.endswith("json"):
                with open(os.path.join(self.template_tnm_Folder, mappingFile)) as f:
                    self.mappingslist.append(json.load(f))
        for mappingFile in sorted(os.listdir(self.tnm_Folder)):
            if mappingFile.endswith("json"):
                with open(os.path.join(self.tnm_Folder, mappingFile)) as f:
                    self.mappingslist.append(json.load(f))

        self.mappingdict = {}
        self.editable_mapping_names = []
        for mapping in self.mappingslist:
            self.mappingdict[mapping[self.tnm_attr_name]] = mapping
            if not mapping[self.tnm_attr_template]:
                self.editable_mapping_names.append(mapping[self.tnm_attr_name])

        if show_menu:
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.tr = tei_reader.TEIReader(show_menu=False)
            self.tng = gb.TEINERGroundtruthBuilder(show_menu=False)
            self.show()
            self.check_rerun_messages()

    def check_rerun_messages(self):
        if "tnm_rerun_save_message" in st.session_state and st.session_state.tnm_rerun_save_message is not None:
            st.session_state.tnm_save_message=st.session_state.tnm_rerun_save_message
            st.session_state.tnm_rerun_save_message = None
            st.experimental_rerun()

    def check_one_time_attributes(self):
        if "tnm_save_message" in st.session_state and st.session_state.tnm_save_message is not None:
            self.tnm_save_message = st.session_state.tnm_save_message
            st.session_state.tnm_save_message = None
        else:
            self.tnm_save_message = None

        if "tnm_reload_aggrids" in st.session_state and st.session_state.tnm_reload_aggrids == True:
            self.tnm_reload_aggrids = True
            st.session_state.tnm_reload_aggrids = False
        else:
            self.tnm_reload_aggrids = False

    def validate_mapping_for_save(self, mapping, mode):
        val = True
        if (
            self.tnm_attr_name not in mapping.keys()
            or mapping[self.tnm_attr_name] is None
            or mapping[self.tnm_attr_name] == ""
        ):
            val = False
            if self.tnm_save_message is None:
                st.error("Please define a name for the mapping before saving!")
        elif (
            os.path.isfile(
                os.path.join(
                    self.tnm_Folder,
                    mapping[self.tnm_attr_name].replace(" ", "_") + ".json",
                )
            )
            and mode != self.tnm_mode_edit
        ):
            val = False
            if self.tnm_save_message is None:
                st.error(f"Choose another name. There is already a mapping with name {mapping[self.tnm_attr_name]}!")
        # clear empty mapping entries
        entities_to_del = []
        for entity in mapping[self.tnm_attr_entity_dict].keys():
            cleared_list = []
            assingned_tag_list = list(mapping[self.tnm_attr_entity_dict][entity])
            for index in range(len(assingned_tag_list)):
                if assingned_tag_list[index][0] is not None and assingned_tag_list[index][0] != "":
                    if " " in assingned_tag_list[index][0]:
                        val = False
                        if self.tnm_save_message is None:
                            st.error(
                                f"For the entity {entity} you defined a tag name ({assingned_tag_list[index][0]}) containing a space character. This is not allowed!"
                            )
                    for attribute in assingned_tag_list[index][1].keys():
                        if (
                            (attribute is None or attribute == "")
                            and assingned_tag_list[index][1][attribute] is not None
                            and assingned_tag_list[index][1][attribute] != ""
                        ):
                            val = False
                            if self.tnm_save_message is None:
                                st.error(
                                    f"For the entity {entity} and tag {assingned_tag_list[index][0]} you defined an attribute value {assingned_tag_list[index][1][attribute]} without a corresponding attribute name. This is not allowed."
                                )
                        elif (
                            attribute is not None
                            and attribute != ""
                            and (
                                assingned_tag_list[index][1][attribute] is None
                                or assingned_tag_list[index][1][attribute] == ""
                            )
                        ):
                            val = False
                            if self.tnm_save_message is None:
                                st.error(
                                    f"For the entity {entity} and tag {mapping[self.tnm_attr_entity_dict][entity][0]} you defined the attribute {attribute} without a value for it. This is not allowed."
                                )
                        elif " " in attribute:
                            val = False
                            if self.tnm_save_message is None:
                                st.error(
                                    f"For the entity {entity} and tag {assingned_tag_list[index][0]} you defined an attribute name ({attribute}) containing a space character. This is not allowed!"
                                )
                        elif " " in assingned_tag_list[index][1][attribute]:
                            val = False
                            if self.tnm_save_message is None:
                                st.error(
                                    f"For the entity {entity} and tag {assingned_tag_list[index][0]} you defined for the attribute {attribute} a value ({assingned_tag_list[index][1][attribute]}) containing a space character. This is not allowed!"
                                )
                    cleared_list.append(assingned_tag_list[index])
            if len(cleared_list) > 0:
                mapping[self.tnm_attr_entity_dict][entity] = cleared_list
            else:
                entities_to_del.append(entity)
        for entity in entities_to_del:
            del mapping[self.tnm_attr_entity_dict][entity]

        if len(mapping[self.tnm_attr_entity_dict].keys()) == 0:
            val = False
            if self.tnm_save_message is None:
                st.error(f"Please define at least one mapping of an entity to a tag. Otherwise there is nothing to save.")

        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tnm][self.tnm_attr_name] == mapping[self.tnm_attr_name]:
                val = False
                if self.tnm_save_message is None:
                    st.error(
                        f"To edit the {menu_TEI_read_mapping} {mapping[self.tnm_attr_name]} is not allowed because it is already used in the Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the mapping to the groundtruth."
                    )
        return val

    def validate_mapping_for_delete(self, mapping):
        val = True
        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tnm][self.tnm_attr_name] == mapping[self.tnm_attr_name]:
                val = False
                if self.tnm_save_message is None:
                    st.error(
                        f"To delete the {menu_TEI_read_mapping} {mapping[self.tnm_attr_name]} is not allowed because it is already used in the Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the mapping to the groundtruth."
                    )
        return val

    def show_editable_attr_value_def(self, attr_value_dict, name):
        st.markdown("Define optionally attributes with values which have to be set for this tag!")
        entry_dict = {"Attributes": [], "Values": []}
        for key in attr_value_dict.keys():
            entry_dict["Attributes"].append(key)
            entry_dict["Values"].append(attr_value_dict[key])
        answer = editable_multi_column_table(
            entry_dict, "tnm_attr_value" + name, openentrys=20, reload=self.tnm_reload_aggrids
        )
        returndict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in returndict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            returndict[answer["Attributes"][i]] = answer["Values"][i]
        return returndict

    def build_tnm_ntd_sel_key(self, mode):
        return (
            "tnm_ntd_sel_"
            + mode
            + ("" if mode == self.tnm_mode_add else st.session_state["tnm_sel_mapping_name_" + mode])
        )

    def build_tnm_sel_edit_entity_key(self, mode):
        return (
            "tnm_ent_" + mode + ("" if mode == self.tnm_mode_add else st.session_state["tnm_sel_mapping_name_" + mode])
        )

    def show_editable_mapping_content(self, mode):
        if mode == self.tnm_mode_edit and len(self.editable_mapping_names) < 1:
            st.info(
                f"There are no self-defined {menu_TEI_read_mapping}s to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            tnm_mapping_dict = {}
            init_tnm_ntd_name = ""
            init_tnm_entity_dict = {}
            if mode in [self.tnm_mode_dupl, self.tnm_mode_edit]:

                def tnm_sel_mapping_name_change(mode):
                    st.session_state.tnm_reload_aggrids = True
                    if "tnm_entity_dict" in st.session_state:
                        del st.session_state["tnm_entity_dict"]

                if self.tnm_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                st.selectbox(
                    label=f"Select a mapping to {mode}!",
                    options=options,
                    key="tnm_sel_mapping_name_" + mode,
                    on_change=tnm_sel_mapping_name_change,
                    args=(mode,),
                )
                tnm_mapping_dict = self.mappingdict[st.session_state["tnm_sel_mapping_name_" + mode]].copy()
                init_tnm_ntd_name = tnm_mapping_dict[self.tnm_attr_ntd][self.ntd.ntd_attr_name]
                init_tnm_entity_dict = tnm_mapping_dict[self.tnm_attr_entity_dict]
                if mode == self.tnm_mode_dupl:
                    tnm_mapping_dict[self.tnm_attr_name] = ""
            if mode == self.tnm_mode_add:
                tnm_mapping_dict[self.tnm_attr_ntd] = {}
                tnm_mapping_dict[self.tnm_attr_entity_dict] = {}
            if mode in [self.tnm_mode_dupl, self.tnm_mode_add]:
                st.text_input(label=f"New {menu_TEI_read_mapping} Name:", key="tnm_name_" + mode)
                tnm_mapping_dict[self.tnm_attr_name] = st.session_state["tnm_name_" + mode]

            def tnm_ntd_change_trigger(mode):
                st.session_state.tnm_reload_aggrids = True
                if self.build_tnm_sel_edit_entity_key(mode) in st.session_state:
                    del st.session_state[self.build_tnm_sel_edit_entity_key(mode)]
                if "tnm_entity_dict" in st.session_state:
                    del st.session_state["tnm_entity_dict"]
                for key in st.session_state:
                    if key.startswith("tnm_tag_def_"):
                        del st.session_state[key]

            st.selectbox(
                label=f"Corresponding {menu_entity_definition}",
                options=list(self.ntd.defdict.keys()),
                key=self.build_tnm_ntd_sel_key(mode),
                index=list(self.ntd.defdict.keys()).index(init_tnm_ntd_name)
                if init_tnm_ntd_name is not None and init_tnm_ntd_name != ""
                else 0,
                on_change=tnm_ntd_change_trigger,
                args=(mode,),
            )
            if self.build_tnm_ntd_sel_key(mode) in st.session_state:
                options = self.ntd.defdict[st.session_state[self.build_tnm_ntd_sel_key(mode)]][
                    self.ntd.ntd_attr_entitylist
                ]
                st.selectbox(
                    label="Define mapping for entity:",
                    options=options,
                    key=self.build_tnm_sel_edit_entity_key(mode),
                )
                st.session_state.tnm_entity_dict = self.edit_entity(
                    mode,
                    st.session_state[self.build_tnm_sel_edit_entity_key(mode)],
                    st.session_state.tnm_entity_dict if "tnm_entity_dict" in st.session_state else init_tnm_entity_dict,
                )

            tnm_mapping_dict[self.tnm_attr_ntd] = self.ntd.defdict[st.session_state[self.build_tnm_ntd_sel_key(mode)]]
            tnm_mapping_dict[self.tnm_attr_entity_dict] = st.session_state.tnm_entity_dict.copy()

            def save_mapping(mapping, mode):
                #clear possible old mappings to old entity definitions
                allowed_entity_list=mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]
                keys_to_delete=[]
                for key in mapping[self.tnm_attr_entity_dict].keys():
                    if key not in allowed_entity_list:
                        keys_to_delete.append(key)
                for key in keys_to_delete:
                    del mapping[self.tnm_attr_entity_dict][key]

                mapping[self.tnm_attr_template] = False
                with open(
                    os.path.join(
                        self.tnm_Folder,
                        mapping[self.tnm_attr_name].replace(" ", "_") + ".json",
                    ),
                    "w+",
                ) as f:
                    json.dump(mapping, f)
                if mode != self.tnm_mode_edit:
                    st.session_state["tnm_name_" + mode] = ""
                # if mode != self.tnm_mode_edit:
                #    del st.session_state["tnm_sel_mapping_name_" + mode]
                for key in st.session_state:
                    if key.startswith("tnm_ntd_sel_"+mode) or key.startswith("tnm_ent_"+mode) or key.startswith("tnm_name_"+mode) or key.startswith("tnm_tag_def_"):
                        del st.session_state[key]
                st.session_state.tnm_rerun_save_message = (
                    f"{menu_TEI_read_mapping} {mapping[self.tnm_attr_name]} succesfully saved!"
                )
                st.session_state.tnm_reload_aggrids = True
                del st.session_state["tnm_entity_dict"]
                if self.build_tnm_sel_edit_entity_key(mode) in st.session_state:
                    del st.session_state[self.build_tnm_sel_edit_entity_key(mode)]

            if self.tnm_save_message is not None:
                st.success(self.tnm_save_message)

            if self.validate_mapping_for_save(tnm_mapping_dict, mode):
                st.button(
                    f"Save {menu_TEI_read_mapping}",
                    key="tnm_save_" + mode,
                    on_click=save_mapping,
                    args=(
                        tnm_mapping_dict,
                        mode,
                    ),
                )

    def edit_entity(self, mode, tnm_edit_entity, cur_entity_dict):
        if tnm_edit_entity not in cur_entity_dict.keys():
            cur_entity_dict[tnm_edit_entity] = [[None, {}]]
        index = 0
        for mapping_entry in cur_entity_dict[tnm_edit_entity]:
            index += 1
            tag_name_key="tnm_tag_def_" + self.build_tnm_ntd_sel_key(mode) + tnm_edit_entity + mode + str(index)
            if tag_name_key not in st.session_state:
                st.session_state[tag_name_key]=mapping_entry[0] if mapping_entry[0] is not None else ""
            st.text_input(
                label="Tag " + str(index),
                key=tag_name_key
            )
            mapping_entry[0]=st.session_state[tag_name_key]
            if mapping_entry[0]:
                mapping_entry[1] = self.show_editable_attr_value_def(
                    mapping_entry[1], tnm_edit_entity + mode + str(index)
                )

        def add_mapping():
            st.session_state.tnm_entity_dict[tnm_edit_entity].append([None, {}])

        st.button("Add another mapping", on_click=add_mapping)
        return cur_entity_dict

    def tei_ner_map_add(self):
        self.show_editable_mapping_content(self.tnm_mode_add)

    def tei_ner_map_dupl(self):
        self.show_editable_mapping_content(self.tnm_mode_dupl)

    def tei_ner_map_edit(self):
        self.show_editable_mapping_content(self.tnm_mode_edit)

    def tei_ner_map_del(self):
        def delete_mapping(mapping):
            os.remove(
                os.path.join(
                    self.tnm_Folder,
                    mapping[self.tnm_attr_name].replace(" ", "_") + ".json",
                )
            )
            st.session_state.tnm_rerun_save_message = (
                f"{menu_TEI_read_mapping} {mapping[self.tnm_attr_name]} succesfully deleted!"
            )
            st.session_state.tnm_reload_aggrids = True
            del st.session_state["tnm_sel_wri_del_name"]
            if (
                "tnm_sel_details_name" in st.session_state
                and mapping[self.tnm_attr_name] == st.session_state.tnm_sel_details_name
            ):
                del st.session_state["tnm_sel_details_name"]
            for mode in [self.tnm_mode_dupl, self.tnm_mode_edit]:
                if "tnm_sel_mapping_name_" + mode in st.session_state:
                    del st.session_state["tnm_sel_mapping_name_" + mode]
            if "tnm_tnm_test" in st.session_state:
                del st.session_state["tnm_tnm_test"]

        if len(self.editable_mapping_names) > 0:
            st.selectbox(
                label="Select a mapping to delete!",
                options=self.editable_mapping_names,
                key="tnm_sel_wri_del_name",
            )
            if self.validate_mapping_for_delete(self.mappingdict[st.session_state.tnm_sel_wri_del_name]):
                st.button(
                    "Delete Selected Mapping",
                    on_click=delete_mapping,
                    args=(self.mappingdict[st.session_state.tnm_sel_wri_del_name],),
                )
        else:
            st.info(f"There are no self-defined {menu_TEI_read_mapping}s to delete!")
        if self.tnm_save_message is not None:
            st.success(self.tnm_save_message)

    def show_edit_environment(self):
        tnm_definer = st.expander(f"Add or edit existing {menu_TEI_read_mapping}", expanded=False)
        with tnm_definer:

            def change_edit_option_trigger():
                st.session_state.tnm_reload_aggrids = True
                if "tnm_entity_dict" in st.session_state:
                    del st.session_state["tnm_entity_dict"]
                for key in st.session_state:
                    if key.startswith("tnm_tag_def_"):
                        del st.session_state[key]

            if self.tnm_save_message is not None:
                st.success(self.tnm_save_message)
            options = {
                f"Add {menu_TEI_read_mapping}": self.tei_ner_map_add,
                f"Duplicate {menu_TEI_read_mapping}": self.tei_ner_map_dupl,
                f"Edit {menu_TEI_read_mapping}": self.tei_ner_map_edit,
                f"Delete {menu_TEI_read_mapping}": self.tei_ner_map_del,
            }
            st.radio(
                label="Edit Options",
                options=tuple(options.keys()),
                index=0,
                key="tnm_edit_options",
                on_change=change_edit_option_trigger,
            )
            options[st.session_state.tnm_edit_options]()

    def mark_entities_in_text(self, text, entitylist, all_entities, show_entity_names):
        newtext = transform_arbitrary_text_to_latex(text)
        colorindex = 0
        for entity in all_entities:
            if entity in entitylist:

                newtext = newtext.replace(
                    "<" + entity + ">",
                    "<**s>$\\text{\\textcolor{" + latex_color_list[colorindex] + "}{",
                )
                if show_entity_names:
                    newtext = newtext.replace("</" + entity + ">", " (" + entity + ")}}$<**e>")
                else:
                    newtext = newtext.replace("</" + entity + ">", "}}$<**e>")
            else:
                newtext = newtext.replace("<" + entity + ">", "").replace("</" + entity + ">", "")
            colorindex += 1
        # workaround for nested entities
        open = 0
        while newtext.find("<**s>$\\text{") >= 0 or newtext.find("}$<**e>") >= 0:
            start = newtext.find("<**s>$\\text{")
            end = newtext.find("}$<**e>")
            if start > 0:
                if start < end:
                    open += 1
                    if open > 1:
                        newtext = newtext.replace("<**s>$\\text{", "", 1)
                    else:
                        newtext = newtext.replace("<**s>$\\text{", "$\\text{", 1)
                else:
                    open += -1
                    if open > 0:
                        newtext = newtext.replace("}$<**e>", "", 1)
                    else:
                        newtext = newtext.replace("}$<**e>", "}$", 1)
            elif end > 0:
                newtext = newtext.replace("}$<**e>", "}$", 1)
        return newtext

    def show_test_environment(self):
        tnm_test_expander = st.expander(f"Test {menu_TEI_read_mapping}", expanded=False)
        with tnm_test_expander:
            st.selectbox(
                label=f"Select a {menu_TEI_reader_config} for the mapping test!",
                options=list(self.tr.configdict.keys()),
                index=0,
                key="tnm_tr_test",
            )
            config = self.tr.configdict[st.session_state.tnm_tr_test]
            st.selectbox(
                label=f"Select a {menu_TEI_read_mapping} to test!",
                options=list(self.mappingdict.keys()),
                index=0,
                key="tnm_tnm_test",
            )
            mapping = self.mappingdict[st.session_state.tnm_tnm_test]
            small_file_selector(
                label="Choose a TEI-File",
                key="tnm_test_TEI_file",
                help=f"Choose a TEI file for testing the chosen {menu_TEI_read_mapping}",
            )

            if st.button(
                f"Test {menu_TEI_read_mapping}",
                key="tnm_button_test",
                help=f"Test {menu_TEI_read_mapping} on the chosen Mapping and TEI-File.",
            ):
                if os.path.isfile(st.session_state.tnm_test_TEI_file):
                    if is_accepted_TEI_filename(st.session_state.tnm_test_TEI_file,True):
                        st.session_state.tnm_last_test_dict = {
                            "teifile": st.session_state.tnm_test_TEI_file,
                            "tr": config.copy(),
                            "tnm": mapping.copy(),
                        }
                else:
                    st.error(f"The chosen path {st.session_state.tnm_test_TEI_file} is not a file!")
                    st.session_state.tnm_last_test_dict = {}

            if "tnm_last_test_dict" in st.session_state and len(st.session_state.tnm_last_test_dict.keys()) > 0:
                tei = tp.TEIFile(
                    st.session_state.tnm_last_test_dict["teifile"],
                    st.session_state.tnm_last_test_dict["tr"],
                    entity_dict=st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_entity_dict],
                )
                col1, col2 = st.columns([0.2, 0.8])
                statistics = tei.get_statistics()
                st.session_state.tnm_test_entity_list = []
                with col1:
                    st.subheader("Tagged Entites:")
                    for entity in sorted(
                        st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]
                    ):
                        if entity in statistics.keys():
                            if st.checkbox(
                                "Show Entity " + entity + " (" + str(statistics[entity][0]) + ")",
                                True,
                                key="tnm" + entity + "text",
                            ):
                                st.session_state.tnm_test_entity_list.append(entity)
                    st.subheader("Display Options:")
                    tnm_test_show_entity_name = st.checkbox(
                        "Display Entity names", False, key="tnm_display_entity_names"
                    )
                    st.subheader("Legend:")
                    index = 0
                    for entity in sorted(
                        st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]
                    ):
                        if entity in statistics.keys():
                            st.write(
                                "$\\color{"
                                + latex_color_list[index % len(latex_color_list)]
                                + "}{\\Large\\bullet}$ "
                                + entity
                            )
                        index += 1

                with col2:
                    st.subheader("Tagged Text Content:")
                    st.write(
                        self.mark_entities_in_text(
                            tei.get_tagged_text(),
                            st.session_state.tnm_test_entity_list,
                            sorted(
                                st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_ntd][
                                    self.ntd.ntd_attr_entitylist
                                ]
                            ),
                            show_entity_names=tnm_test_show_entity_name,
                        )
                    )
                if config[self.tr.tr_config_attr_use_notes]:
                    col1_note, col2_note = st.columns([0.2, 0.8])
                    note_statistics = tei.get_note_statistics()
                    st.session_state.tnm_test_note_entity_list = []
                    with col1_note:
                        st.subheader("Tagged Entites:")
                        for entity in sorted(
                            st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]
                        ):
                            if entity in note_statistics.keys():
                                if st.checkbox(
                                    "Show Entity " + entity + " (" + str(note_statistics[entity][0]) + ")",
                                    True,
                                    key="tnm" + entity + "note",
                                ):
                                    st.session_state.tnm_test_note_entity_list.append(entity)
                        st.subheader("Display Options:")
                        tnm_test_note_show_entity_name = st.checkbox(
                            "Display Entity names",
                            False,
                            key="tnm_display_entity_names_note",
                        )
                        st.subheader("Legend: ")
                        index = 0
                        for entity in sorted(
                            st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]
                        ):
                            if entity in note_statistics.keys():
                                st.write(
                                    "$\\color{"
                                    + latex_color_list[index % len(latex_color_list)]
                                    + "}{\\bullet}$ "
                                    + entity
                                )
                            index += 1

                    with col2_note:
                        st.subheader("Tagged Note Content:")
                        st.write(
                            self.mark_entities_in_text(
                                tei.get_tagged_notes(),
                                st.session_state.tnm_test_note_entity_list,
                                sorted(
                                    st.session_state.tnm_last_test_dict["tnm"][self.tnm_attr_ntd][
                                        self.ntd.ntd_attr_entitylist
                                    ]
                                ),
                                show_entity_names=tnm_test_note_show_entity_name,
                            )
                        )

    def build_tnm_tablestring(self):
        tablestring = f"Name | {menu_entity_definition} | Template \n -----|-------|-------"
        for mapping in self.mappingslist:
            if mapping[self.tnm_attr_template]:
                template = "yes"
            else:
                template = "no"
            tablestring += (
                "\n "
                + mapping[self.tnm_attr_name]
                + " | "
                + mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_name]
                + " | "
                + template
            )
        return tablestring

    def build_tnm_entity_detail_string(self, entity_detail):
        tag_string = ""
        attr_string = ""
        for tag_def in entity_detail:
            cur_len = len(tag_def[1].keys())
            tag_string += tag_def[0]
            if cur_len == 0:
                attr_string += " "
            else:
                for attr in tag_def[1].keys():
                    attr_string += attr + "=" + tag_def[1][attr] + ","
                attr_string = attr_string[:-1]
            tag_string += " <br> "
            attr_string += " <br> "
        return tag_string + " | " + attr_string

    def build_tnm_detail_tablestring(self, tnm):
        tablestring = "Entity | Tag | Attributes \n -----|-------|-------"
        for entity in tnm[self.tnm_attr_entity_dict].keys():
            tablestring += (
                "\n " + entity + " | " + self.build_tnm_entity_detail_string(tnm[self.tnm_attr_entity_dict][entity])
            )
        return tablestring

    def show_tnms(self):
        tnm_show = st.expander(f"Existing {menu_TEI_read_mapping}s", expanded=True)
        with tnm_show:
            st.markdown(self.build_tnm_tablestring())
            st.selectbox(
                label=f"Choose a mapping for displaying its details:",
                options=list(self.mappingdict.keys()),
                key="tnm_sel_details_name",
                index=0,
            )
            if "tnm_sel_details_name" in st.session_state:
                cur_sel_mapping = self.mappingdict[st.session_state.tnm_sel_details_name]
                st.markdown(
                    self.build_tnm_detail_tablestring(cur_sel_mapping),
                    unsafe_allow_html=True,
                )
                if len(cur_sel_mapping[self.tnm_attr_entity_dict].keys()) < len(
                    cur_sel_mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]
                ):
                    st.warning(
                        f"Warning: The Mapping {cur_sel_mapping[self.tnm_attr_name]} is possibly incomplete. Not every entity of the corresponding task {cur_sel_mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_name]} is assigned to at least one tag."
                    )
            st.markdown(" ")  # only for layouting reasons (placeholder)

    def show(self):
        st.latex("\\text{\Huge{" + menu_TEI_read_mapping + "}}")
        col1, col2 = st.columns(2)
        with col1:
            self.show_tnms()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
