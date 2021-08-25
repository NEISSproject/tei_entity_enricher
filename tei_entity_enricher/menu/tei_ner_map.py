import streamlit as st
import json
import os

from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
    transform_arbitrary_text_to_latex,
    latex_color_list,
)
from tei_entity_enricher.util.components import (
    editable_multi_column_table,
    small_file_selector,
    selectbox_widget,
    text_input_widget,
    radio_widget,
)
import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_gb as gb
import tei_entity_enricher.util.tei_parser as tp
from dataclasses import dataclass
from typing import List, Dict
from dataclasses_json import dataclass_json


@dataclass
@dataclass_json
class TEINERMapParams:
    tnm_selected_display_tnm_name: str = None
    tnm_sel_wri_del_name: str = None
    tnm_mode: str = None
    tnm_sel_mapping_name: str = None
    tnm_name: str = None
    tnm_ntd_name: str = None
    tnm_edit_entity: str = None
    tnm_entity_dict: List = None

    tnm_test_selected_config_name: str = None
    tnm_test_selected_mapping_name: str = None
    tnm_teifile: str = None
    tnm_last_test_dict: Dict = None
    tnm_test_entity_list: List = None
    tnm_test_note_entity_list = None
    tnm_edit_options: str = None


@st.cache(allow_output_mutation=True)
def get_params() -> TEINERMapParams:
    return TEINERMapParams()


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

    @property
    def tei_ner_map_params(self) -> TEINERMapParams:
        return get_params()

    def validate_and_saving_mapping(self, mapping, mode):
        val = True
        if (
            self.tnm_attr_name not in mapping.keys()
            or mapping[self.tnm_attr_name] is None
            or mapping[self.tnm_attr_name] == ""
        ):
            val = False
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
                            st.error(
                                f"For the entity {entity} and tag {mapping[self.tnm_attr_entity_dict][entity][0]} you defined the attribute {attribute} without a value for it. This is not allowed."
                            )
                        elif " " in attribute:
                            val = False
                            st.error(
                                f"For the entity {entity} and tag {assingned_tag_list[index][0]} you defined an attribute name ({attribute}) containing a space character. This is not allowed!"
                            )
                        elif " " in assingned_tag_list[index][1][attribute]:
                            val = False
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
            st.error(f"Please define at least one mapping of an entity to a tag. Otherwise there is nothing to save.")

        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tnm][self.tnm_attr_name] == mapping[self.tnm_attr_name]:
                val = False
                st.error(
                    f"To edit the Entity Mapping {mapping[self.tnm_attr_name]} is not allowed because it is already used in the TEI NER Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the mapping to the groundtruth."
                )

        if val:
            mapping[self.tnm_attr_template] = False
            with open(
                os.path.join(
                    self.tnm_Folder,
                    mapping[self.tnm_attr_name].replace(" ", "_") + ".json",
                ),
                "w+",
            ) as f:
                json.dump(mapping, f)
            self.reset_tnm_edit_states()
            st.experimental_rerun()

    def validate_and_delete_mapping(self, mapping):
        val = True
        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tnm][self.tnm_attr_name] == mapping[self.tnm_attr_name]:
                val = False
                st.error(
                    f"To delete the Entity Mapping {mapping[self.tnm_attr_name]} is not allowed because it is already used in the TEI NER Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the mapping to the groundtruth."
                )

        if val:
            os.remove(
                os.path.join(
                    self.tnm_Folder,
                    mapping[self.tnm_attr_name].replace(" ", "_") + ".json",
                )
            )
            self.reset_tnm_edit_states()
            self.tei_ner_map_params.tnm_sel_mapping_name = None
            self.tei_ner_map_params.tnm_sel_wri_del_name = None
            if mapping[self.tnm_attr_name] == self.tei_ner_map_params.tnm_selected_display_tnm_name:
                self.tei_ner_map_params.tnm_selected_display_tnm_name = None
            st.experimental_rerun()

    def reset_tnm_edit_states(self):
        self.tei_ner_map_params.tnm_name = None
        self.tei_ner_map_params.tnm_ntd_name = None
        self.tei_ner_map_params.tnm_entity_dict = None

    def show_editable_attr_value_def(self, attr_value_dict, name):
        st.markdown("Define optionally attributes with values which have to be set for this tag!")
        entry_dict = {"Attributes": [], "Values": []}
        for key in attr_value_dict.keys():
            entry_dict["Attributes"].append(key)
            entry_dict["Values"].append(attr_value_dict[key])
        answer = editable_multi_column_table(entry_dict, "tnm_attr_value" + name, openentrys=20)
        returndict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in returndict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            returndict[answer["Attributes"][i]] = answer["Values"][i]
        return returndict

    def show_editable_mapping_content(self, mode):
        if mode == self.tnm_mode_edit and len(self.editable_mapping_names) < 1:
            st.info(
                "There are no self-defined TEI Read NER Entity Mappings to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            if self.tei_ner_map_params.tnm_mode != mode:
                self.reset_tnm_edit_states()
                self.tei_ner_map_params.tnm_sel_mapping_name = None
            self.tei_ner_map_params.tnm_mode = mode
            tnm_mapping_dict = {}
            init_tnm_ntd_name = self.tei_ner_map_params.tnm_ntd_name
            init_tnm_entity_dict = {}
            if mode in [self.tnm_mode_dupl, self.tnm_mode_edit]:
                if self.tnm_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                selected_tnm_name = selectbox_widget(
                    f"Select a mapping to {mode}!",
                    options,
                    options.index(self.tei_ner_map_params.tnm_sel_mapping_name)
                    if self.tei_ner_map_params.tnm_sel_mapping_name
                    else 0,
                    key="tnm" + mode,
                )
                if self.tei_ner_map_params.tnm_sel_mapping_name != selected_tnm_name:
                    self.reset_tnm_edit_states()
                self.tei_ner_map_params.tnm_sel_mapping_name = selected_tnm_name
                tnm_mapping_dict = self.mappingdict[selected_tnm_name].copy()
                init_tnm_ntd_name = tnm_mapping_dict[self.tnm_attr_ntd][self.ntd.ntd_attr_name]
                init_tnm_entity_dict = tnm_mapping_dict[self.tnm_attr_entity_dict]
                if mode == self.tnm_mode_dupl:
                    tnm_mapping_dict[self.tnm_attr_name] = ""
            else:
                selected_tnm_name = ""
            if mode == self.tnm_mode_add:
                tnm_mapping_dict[self.tnm_attr_ntd] = {}
                tnm_mapping_dict[self.tnm_attr_entity_dict] = {}
            if mode in [self.tnm_mode_dupl, self.tnm_mode_add]:
                self.tei_ner_map_params.tnm_name = text_input_widget(
                    "New TEI Read NER Entity Mapping Name:", self.tei_ner_map_params.tnm_name or ""
                )
                if self.tei_ner_map_params.tnm_name:
                    tnm_mapping_dict[self.tnm_attr_name] = self.tei_ner_map_params.tnm_name

            sel_tnm_ntd_name = selectbox_widget(
                "Corresponding NER task definition",
                list(self.ntd.defdict.keys()),
                list(self.ntd.defdict.keys()).index(init_tnm_ntd_name) if init_tnm_ntd_name else 0,
                key="tnm_ntd_sel" + mode + selected_tnm_name,
            )
            if self.tei_ner_map_params.tnm_ntd_name and sel_tnm_ntd_name != self.tei_ner_map_params.tnm_ntd_name:
                self.tei_ner_map_params.tnm_entity_dict = None
                self.tei_ner_map_params.tnm_edit_entity = None
            self.tei_ner_map_params.tnm_ntd_name = sel_tnm_ntd_name
            if self.tei_ner_map_params.tnm_ntd_name:
                options = self.ntd.defdict[self.tei_ner_map_params.tnm_ntd_name][self.ntd.ntd_attr_entitylist]
                self.tei_ner_map_params.tnm_edit_entity = selectbox_widget(
                    "Define mapping for entity:",
                    options,
                    index=options.index(self.tei_ner_map_params.tnm_edit_entity)
                    if self.tei_ner_map_params.tnm_edit_entity
                    else 0,
                    key="tnm_ent" + mode,
                )
                if self.tei_ner_map_params.tnm_edit_entity:
                    self.tei_ner_map_params.tnm_entity_dict = self.edit_entity(
                        mode,
                        self.tei_ner_map_params.tnm_edit_entity,
                        self.tei_ner_map_params.tnm_entity_dict if self.tei_ner_map_params.tnm_entity_dict else init_tnm_entity_dict,
                    )

            if st.button("Save TEI Read NER Entity Mapping", key=mode):
                tnm_mapping_dict[self.tnm_attr_ntd] = self.ntd.defdict[self.tei_ner_map_params.tnm_ntd_name]
                tnm_mapping_dict[self.tnm_attr_entity_dict] = self.tei_ner_map_params.tnm_entity_dict.copy()
                self.validate_and_saving_mapping(tnm_mapping_dict, mode)

    def edit_entity(self, mode, tnm_edit_entity, cur_entity_dict):
        if tnm_edit_entity not in cur_entity_dict.keys():
            cur_entity_dict[tnm_edit_entity] = [[None, {}]]
        index = 0
        for mapping_entry in cur_entity_dict[tnm_edit_entity]:
            index += 1
            mapping_entry[0] = text_input_widget(
                "Tag " + str(index),
                mapping_entry[0] or "",
                key="tnm" + self.tei_ner_map_params.tnm_ntd_name + tnm_edit_entity + mode + str(index),
            )
            if mapping_entry[0]:
                mapping_entry[1] = self.show_editable_attr_value_def(
                    mapping_entry[1], tnm_edit_entity + mode + str(index)
                )
        if st.button("Add another mapping"):
            cur_entity_dict[tnm_edit_entity].append([None, {}])
            st.experimental_rerun()
        return cur_entity_dict

    def tei_ner_map_add(self):
        self.show_editable_mapping_content(self.tnm_mode_add)

    def tei_ner_map_dupl(self):
        self.show_editable_mapping_content(self.tnm_mode_dupl)

    def tei_ner_map_edit(self):
        self.show_editable_mapping_content(self.tnm_mode_edit)

    def tei_ner_map_del(self):
        if len(self.editable_mapping_names) > 0:
            self.tei_ner_map_params.tnm_sel_wri_del_name = selectbox_widget(
                "Select a mapping to delete!",
                self.editable_mapping_names,
                index=self.editable_mapping_names.index(self.tei_ner_map_params.tnm_sel_wri_del_name)
                if self.tei_ner_map_params.tnm_sel_wri_del_name
                else 0,
            )
            if st.button("Delete Selected Mapping"):
                self.validate_and_delete_mapping(self.mappingdict[self.tei_ner_map_params.tnm_sel_wri_del_name])
        else:
            st.info("There are no self-defined TEI Read NER Entity mappings to delete!")

    def show_edit_environment(self):
        tnm_definer = st.expander("Add or edit existing TEI Read NER Entity Mapping", expanded=False)
        with tnm_definer:
            options = {
                "Add TEI Read NER Entity Mapping": self.tei_ner_map_add,
                "Duplicate TEI Read NER Entity Mapping": self.tei_ner_map_dupl,
                "Edit TEI Read NER Entity Mapping": self.tei_ner_map_edit,
                "Delete TEI Read NER Entity Mapping": self.tei_ner_map_del,
            }
            self.tei_ner_map_params.tnm_edit_options = radio_widget(
                "Edit Options",
                tuple(options.keys()),
                tuple(options.keys()).index(self.tei_ner_map_params.tnm_edit_options)
                if self.tei_ner_map_params.tnm_edit_options
                else 0,
            )
            options[self.tei_ner_map_params.tnm_edit_options]()

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
        tnm_test_expander = st.expander("Test TEI Read NER Entity Mapping", expanded=False)
        with tnm_test_expander:
            self.tei_ner_map_params.tnm_test_selected_config_name = selectbox_widget(
                "Select a TEI Reader Config for the mapping test!",
                list(self.tr.configdict.keys()),
                index=list(self.tr.configdict.keys()).index(self.tei_ner_map_params.tnm_test_selected_config_name)
                if self.tei_ner_map_params.tnm_test_selected_config_name
                else 0,
                key="tnm_tr_test",
            )
            config = self.tr.configdict[self.tei_ner_map_params.tnm_test_selected_config_name]
            self.tei_ner_map_params.tnm_test_selected_mapping_name = selectbox_widget(
                "Select a TEI Read NER Entity Mapping to test!",
                list(self.mappingdict.keys()),
                index=list(self.mappingdict.keys()).index(self.tei_ner_map_params.tnm_test_selected_mapping_name)
                if self.tei_ner_map_params.tnm_test_selected_mapping_name
                else 0,
                key="tnm_tnm_test",
            )
            mapping = self.mappingdict[self.tei_ner_map_params.tnm_test_selected_mapping_name]
            self.tei_ner_map_params.tnm_teifile = small_file_selector(
                label="Choose a TEI-File",
                value=self.tei_ner_map_params.tnm_teifile if self.tei_ner_map_params.tnm_teifile else local_save_path,
                key="tnm_test_choos_TEI",
                help="Choose a TEI file for testing the chosen TEI Read Entity Mapping",
            )
            if st.button(
                "Test TEI Read Entity Mapping",
                key="tnm_Button_Test",
                help="Test TEI Read Entity Mapping on the chosen Mapping and TEI-File.",
            ):
                if os.path.isfile(self.tei_ner_map_params.tnm_teifile):
                    self.tei_ner_map_params.tnm_last_test_dict = {
                        "teifile": self.tei_ner_map_params.tnm_teifile,
                        "tr": config,
                        "tnm": self.tnm_attr_entity_dict,
                    }
                else:
                    st.error(f"The chosen path {self.tei_ner_map_params.tnm_teifile} is not a file!")
                    self.tei_ner_map_params.tnm_last_test_dict = {}
            if (
                self.tei_ner_map_params.tnm_last_test_dict
                and len(self.tei_ner_map_params.tnm_last_test_dict.keys()) > 0
            ):
                tei = tp.TEIFile(
                    self.tei_ner_map_params.tnm_last_test_dict["teifile"],
                    self.tei_ner_map_params.tnm_last_test_dict["tr"],
                    entity_dict=mapping[self.tei_ner_map_params.tnm_last_test_dict["tnm"]],
                )
                col1, col2 = st.columns([0.2, 0.8])
                statistics = tei.get_statistics()
                self.tei_ner_map_params.tnm_test_entity_list = []
                with col1:
                    st.subheader("Tagged Entites:")
                    for entity in sorted(mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]):
                        if entity in statistics.keys():
                            if st.checkbox(
                                "Show Entity " + entity + " (" + str(statistics[entity][0]) + ")",
                                True,
                                key="tnm" + entity + "text",
                            ):
                                self.tei_ner_map_params.tnm_test_entity_list.append(entity)
                    st.subheader("Display Options:")
                    tnm_test_show_entity_name = st.checkbox(
                        "Display Entity names", False, key="tnm_display_entity_names"
                    )
                    st.subheader("Legend:")
                    index = 0
                    for entity in sorted(mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]):
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
                            self.tei_ner_map_params.tnm_test_entity_list,
                            sorted(mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]),
                            show_entity_names=tnm_test_show_entity_name,
                        )
                    )
                if config[self.tr.tr_config_attr_use_notes]:
                    col1_note, col2_note = st.columns([0.2, 0.8])
                    note_statistics = tei.get_note_statistics()
                    self.tei_ner_map_params.tnm_test_note_entity_list = []
                    with col1_note:
                        st.subheader("Tagged Entites:")
                        for entity in sorted(mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]):
                            if entity in note_statistics.keys():
                                if st.checkbox(
                                    "Show Entity " + entity + " (" + str(note_statistics[entity][0]) + ")",
                                    True,
                                    key="tnm" + entity + "note",
                                ):
                                    self.tei_ner_map_params.tnm_test_note_entity_list.append(entity)
                        st.subheader("Display Options:")
                        tnm_test_note_show_entity_name = st.checkbox(
                            "Display Entity names",
                            False,
                            key="tnm_display_entity_names_note",
                        )
                        st.subheader("Legend: ")
                        index = 0
                        for entity in sorted(mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]):
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
                                self.tei_ner_map_params.tnm_test_note_entity_list,
                                sorted(mapping[self.tnm_attr_ntd][self.ntd.ntd_attr_entitylist]),
                                show_entity_names=tnm_test_note_show_entity_name,
                            )
                        )

    def build_tnm_tablestring(self):
        tablestring = "Name | NER Task | Template \n -----|-------|-------"
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
        tnm_show = st.expander("Existing TEI Read NER Entity Mappings", expanded=True)
        with tnm_show:
            st.markdown(self.build_tnm_tablestring())
            self.tei_ner_map_params.tnm_selected_display_tnm_name = selectbox_widget(
                f"Choose a mapping for displaying its details:",
                list(self.mappingdict.keys()),
                key="tnm_details",
                index=list(self.mappingdict.keys()).index(self.tei_ner_map_params.tnm_selected_display_tnm_name)
                if self.tei_ner_map_params.tnm_selected_display_tnm_name
                else 0,
            )
            if self.tei_ner_map_params.tnm_selected_display_tnm_name:
                cur_sel_mapping = self.mappingdict[self.tei_ner_map_params.tnm_selected_display_tnm_name]
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
        st.latex("\\text{\Huge{TEI Read NER Entity Mapping}}")
        col1, col2 = st.columns(2)
        with col1:
            self.show_tnms()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
