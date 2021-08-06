import streamlit as st
import json
import os

from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
    get_listoutput,
    transform_arbitrary_text_to_latex,
    latex_color_list,
)
from tei_entity_enricher.util.components import (
    editable_multi_column_table,
    editable_single_column_table,
    selectbox_widget,
    text_input_widget,
    radio_widget,
    small_file_selector,
)
import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.util.tei_parser as tp
from dataclasses import dataclass
from typing import List, Dict
from dataclasses_json import dataclass_json


@dataclass
@dataclass_json
class TEINERWriterParams:
    tnw_selected_display_tnw_name: str = None
    tnw_edit_options: str = None
    tnw_sel_wri_del_name: str = None
    tnw_mode: str = None
    tnw_ntd_name: str = None
    tnw_name: str = None
    tnw_sel_mapping_name: str = None
    tnw_fixed_list: List[str] = None
    tnw_entity_dict: List = None
    tnw_edit_entity: str = None
    tnw_test_selected_config_name: str = None
    tnw_test_selected_mapping_name: str = None
    tnw_teifile: str = None
    tnw_last_test_dict: Dict = None
    tnw_test_entity_list: List = None
    tnw_test_note_entity_list: List = None


@st.cache(allow_output_mutation=True)
def get_params() -> TEINERWriterParams:
    return TEINERWriterParams()


class TEINERPredWriteMap:
    def __init__(self, show_menu=True):
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
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.tr = tei_reader.TEIReader(show_menu=False)
            self.show()

    @property
    def tei_ner_writer_params(self) -> TEINERWriterParams:
        return get_params()

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
                    st.error(f"You defined an fixed tag ({fix_tag}) containing a space character. This is not allowed!")
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
                        attribute is not None
                        and attribute != ""
                        and (
                            mapping[self.tnw_attr_entity_dict][entity][1][attribute] is None
                            or mapping[self.tnw_attr_entity_dict][entity][1][attribute] == ""
                        )
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
            self.tei_ner_writer_params.tnw_sel_mapping_name = None
            self.tei_ner_writer_params.tnw_sel_wri_del_name = None
            if mapping[self.tnw_attr_name] == self.tei_ner_writer_params.tnw_selected_display_tnw_name:
                self.tei_ner_writer_params.tnw_selected_display_tnw_name = None
            st.experimental_rerun()

    def reset_tnw_edit_states(self):
        self.tei_ner_writer_params.tnw_name = None
        self.tei_ner_writer_params.tnw_ntd_name = None
        self.tei_ner_writer_params.tnw_fixed_list = None
        self.tei_ner_writer_params.tnw_entity_dict = None
        self.tei_ner_writer_params.tnw_edit_entity = None

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
            if self.tei_ner_writer_params.tnw_mode != mode:
                self.reset_tnw_edit_states()
            self.tei_ner_writer_params.tnw_mode = mode
            tnw_mapping_dict = {}
            init_tnw_ntd_name = self.tei_ner_writer_params.tnw_ntd_name
            init_tnw_entity_dict = {}
            if mode in [self.tnw_mode_dupl, self.tnw_mode_edit]:
                if self.tnw_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                selected_tnw_name = selectbox_widget(
                    f"Select a mapping to {mode}!",
                    options,
                    options.index(self.tei_ner_writer_params.tnw_sel_mapping_name)
                    if self.tei_ner_writer_params.tnw_sel_mapping_name
                    else 0,
                    key="tnw" + mode,
                )
                if self.tei_ner_writer_params.tnw_sel_mapping_name != selected_tnw_name:
                    self.reset_tnw_edit_states()
                self.tei_ner_writer_params.tnw_sel_mapping_name = selected_tnw_name
                tnw_mapping_dict = self.mappingdict[selected_tnw_name].copy()
                init_tnw_ntd_name = tnw_mapping_dict[self.tnw_attr_ntd][self.ntd.ntd_attr_name]
                init_tnw_entity_dict = tnw_mapping_dict[self.tnw_attr_entity_dict]
                if mode == self.tnw_mode_dupl:
                    tnw_mapping_dict[self.tnw_attr_name] = ""
            else:
                selected_tnw_name = ""
            if mode == self.tnw_mode_add:
                tnw_mapping_dict[self.tnw_attr_ntd] = {}
                tnw_mapping_dict[self.tnw_attr_entity_dict] = {}
                tnw_mapping_dict[self.tnw_attr_fixed_tags] = []
            if mode in [self.tnw_mode_dupl, self.tnw_mode_add]:
                self.tei_ner_writer_params.tnw_name = text_input_widget(
                    "New TEI NER Prediction Writer Mapping Name:", self.tei_ner_writer_params.tnw_name or ""
                )
                if self.tei_ner_writer_params.tnw_name:
                    tnw_mapping_dict[self.tnw_attr_name] = self.tei_ner_writer_params.tnw_name
            sel_tnw_ntd_name = selectbox_widget(
                "Corresponding NER task definition",
                list(self.ntd.defdict.keys()),
                list(self.ntd.defdict.keys()).index(init_tnw_ntd_name) if init_tnw_ntd_name else 0,
                key="tnw_ntd_sel" + mode + selected_tnw_name,
            )
            if self.tei_ner_writer_params.tnw_ntd_name and sel_tnw_ntd_name != self.tei_ner_writer_params.tnw_ntd_name:
                self.tei_ner_writer_params.tnw_entity_dict = None
                self.tei_ner_writer_params.tnw_edit_entity = None
            self.tei_ner_writer_params.tnw_ntd_name = sel_tnw_ntd_name
            init_fixed_list = tnw_mapping_dict[self.tnw_attr_fixed_tags]
            self.tei_ner_writer_params.tnw_fixed_list = self.show_editable_fixed_tags(
                self.tei_ner_writer_params.tnw_fixed_list
                if self.tei_ner_writer_params.tnw_fixed_list
                else init_fixed_list,
                mode,
                (tnw_mapping_dict[self.tnw_attr_name] if self.tnw_attr_name in tnw_mapping_dict.keys() else "")
                + selected_tnw_name,
            )
            if self.tei_ner_writer_params.tnw_ntd_name:
                options = self.ntd.defdict[self.tei_ner_writer_params.tnw_ntd_name][self.ntd.ntd_attr_entitylist]
                self.tei_ner_writer_params.tnw_edit_entity = selectbox_widget(
                    "Define mapping for entity:",
                    options,
                    key="tnw_ent" + mode + selected_tnw_name,
                    index=options.index(self.tei_ner_writer_params.tnw_edit_entity)
                    if self.tei_ner_writer_params.tnw_edit_entity
                    else 0,
                )
                if self.tei_ner_writer_params.tnw_edit_entity:
                    self.tei_ner_writer_params.tnw_entity_dict = self.edit_entity(
                        mode,
                        self.tei_ner_writer_params.tnw_edit_entity,
                        self.tei_ner_writer_params.tnw_entity_dict
                        if self.tei_ner_writer_params.tnw_entity_dict
                        else init_tnw_entity_dict,
                    )

            if st.button("Save TEI NER Prediction Writer Mapping", key=mode):
                tnw_mapping_dict[self.tnw_attr_ntd] = self.ntd.defdict[self.tei_ner_writer_params.tnw_ntd_name]
                tnw_mapping_dict[self.tnw_attr_fixed_tags] = self.tei_ner_writer_params.tnw_fixed_list
                tnw_mapping_dict[self.tnw_attr_entity_dict] = self.tei_ner_writer_params.tnw_entity_dict.copy()
                self.validate_and_saving_mapping(tnw_mapping_dict, mode)

    def edit_entity(self, mode, tnw_edit_entity, cur_entity_dict):
        if tnw_edit_entity not in cur_entity_dict.keys():
            cur_entity_dict[tnw_edit_entity] = [None, {}]
        mapping_entry = cur_entity_dict[tnw_edit_entity]
        mapping_entry[0] = text_input_widget(
            "Tag",
            mapping_entry[0] or "",
            key="tnw" + self.tei_ner_writer_params.tnw_ntd_name + tnw_edit_entity + mode,
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
        if len(self.editable_mapping_names) > 0:
            self.tei_ner_writer_params.tnw_sel_wri_del_name = selectbox_widget(
                "Select a mapping to delete!",
                self.editable_mapping_names,
                index=self.editable_mapping_names.index(self.tei_ner_writer_params.tnw_sel_wri_del_name)
                if self.tei_ner_writer_params.tnw_sel_wri_del_name
                else 0,
            )
            if st.button("Delete Selected Mapping"):
                self.validate_and_delete_mapping(self.mappingdict[self.tei_ner_writer_params.tnw_sel_wri_del_name])
        else:
            st.info("There are no self-defined TEI NER Prediction Writer mapping to delete!")

    def show_edit_environment(self):
        tnw_definer = st.expander("Add or edit existing TEI NER Prediction Writer Mapping", expanded=False)
        with tnw_definer:
            options = {
                "Add TEI NER Prediction Writer Mapping": self.tei_ner_map_add,
                "Duplicate TEI NER Prediction Writer Mapping": self.tei_ner_map_dupl,
                "Edit TEI NER Prediction Writer Mapping": self.tei_ner_map_edit,
                "Delete TEI NER Prediction Writer Mapping": self.tei_ner_map_del,
            }
            self.tei_ner_writer_params.tnw_edit_options = radio_widget(
                "Edit Options",
                tuple(options.keys()),
                tuple(options.keys()).index(self.tei_ner_writer_params.tnw_edit_options)
                if self.tei_ner_writer_params.tnw_edit_options
                else 0,
            )
            options[self.tei_ner_writer_params.tnw_edit_options]()

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
                attr_string += attr + "=" + entity_detail[1][attr] + ", "
            attr_string = attr_string[:-2]
        return tag_string + " | " + attr_string

    def build_tnw_detail_tablestring(self, tnw):
        tablestring = "Entity | Tag | Attributes \n -----|-------|-------"
        for entity in tnw[self.tnw_attr_entity_dict].keys():
            tablestring += (
                "\n " + entity + " | " + self.build_tnw_entity_detail_string(tnw[self.tnw_attr_entity_dict][entity])
            )
        return tablestring

    def show_tnws(self):
        tnw_show = st.expander("Existing TEI NER Prediction Writer Mappings", expanded=True)
        with tnw_show:
            st.markdown(self.build_tnw_tablestring())
            self.tei_ner_writer_params.tnw_selected_display_tnw_name = selectbox_widget(
                f"Choose a mapping for displaying its details:",
                list(self.mappingdict.keys()),
                key="tnw_details",
                index=list(self.mappingdict.keys()).index(self.tei_ner_writer_params.tnw_selected_display_tnw_name)
                if self.tei_ner_writer_params.tnw_selected_display_tnw_name
                else 0,
            )
            if self.tei_ner_writer_params.tnw_selected_display_tnw_name:
                cur_sel_mapping = self.mappingdict[self.tei_ner_writer_params.tnw_selected_display_tnw_name]
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
            st.markdown(" ")  # only for layouting reasons (placeholder)
            
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
        tnw_test_expander = st.expander("Test TEI NER Prediction Writer Mapping", expanded=False)
        with tnw_test_expander:
            self.tei_ner_writer_params.tnw_test_selected_config_name = selectbox_widget(
                "Select a TEI Reader Config for the mapping test!",
                list(self.tr.configdict.keys()),
                index=list(self.tr.configdict.keys()).index(self.tei_ner_writer_params.tnw_test_selected_config_name)
                if self.tei_ner_writer_params.tnw_test_selected_config_name
                else 0,
                key="tnw_tr_test",
            )
            config = self.tr.configdict[self.tei_ner_writer_params.tnw_test_selected_config_name]
            self.tei_ner_writer_params.tnw_test_selected_mapping_name = selectbox_widget(
                "Select a TEI NER Prediction Writer Mapping to test!",
                list(self.mappingdict.keys()),
                index=list(self.mappingdict.keys()).index(self.tei_ner_writer_params.tnw_test_selected_mapping_name)
                if self.tei_ner_writer_params.tnw_test_selected_mapping_name
                else 0,
                key="tnw_tnw_test",
            )
            mapping = self.mappingdict[self.tei_ner_writer_params.tnw_test_selected_mapping_name]
            self.tei_ner_writer_params.tnw_teifile = small_file_selector(
                label="Choose a TEI-File",
                value=self.tei_ner_writer_params.tnw_teifile if self.tei_ner_writer_params.tnw_teifile else local_save_path,
                key="tnw_test_choose_TEI",
                help="Choose a TEI file for testing the chosen TEI NER Prediction Writer Mapping",
            )
            if st.button(
                "Test TEI NER Prediction Writer Mapping",
                key="tnw_Button_Test",
                help="Test TEI NER Prediction Writer Mapping on the chosen Mapping and TEI-File.",
            ):
                if os.path.isfile(self.tei_ner_writer_params.tnw_teifile):
                    self.tei_ner_writer_params.tnw_last_test_dict = {
                        "teifile": self.tei_ner_writer_params.tnw_teifile,
                        "tr": config,
                        "tnw": self.tnw_attr_entity_dict,
                    }
                else:
                    st.error(f"The chosen path {self.tei_ner_writer_params.tnw_teifile} is not a file!")
                    self.tei_ner_writer_params.tnw_last_test_dict = {}
            if self.tei_ner_writer_params.tnw_last_test_dict and len(self.tei_ner_writer_params.tnw_last_test_dict.keys()) > 0:
                tei = tp.TEIFile(
                    self.tei_ner_writer_params.tnw_last_test_dict["teifile"],
                    self.tei_ner_writer_params.tnw_last_test_dict["tr"],
                    entity_dict=mapping[self.tei_ner_writer_params.tnw_last_test_dict["tnw"]],
                )
                col1, col2 = st.columns([0.2, 0.8])
                statistics = tei.get_statistics()
                self.tei_ner_writer_params.tnw_test_entity_list = []
                with col1:
                    st.subheader("Tagged Entites:")
                    for entity in sorted(mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]):
                        if entity in statistics.keys():
                            if st.checkbox(
                                "Show Entity " + entity + " (" + str(statistics[entity][0]) + ")",
                                True,
                                key="tnw" + entity + "text",
                            ):
                                self.tei_ner_writer_params.tnw_test_entity_list.append(entity)
                    st.subheader("Display Options:")
                    tnw_test_show_entity_name = st.checkbox(
                        "Display Entity names", False, key="tnw_display_entity_names"
                    )
                    st.subheader("Legend:")
                    index = 0
                    for entity in sorted(mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]):
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
                            self.tei_ner_writer_params.tnw_test_entity_list,
                            sorted(mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]),
                            show_entity_names=tnw_test_show_entity_name,
                        )
                    )
                if config[self.tr.tr_config_attr_use_notes]:
                    col1_note, col2_note = st.columns([0.2, 0.8])
                    note_statistics = tei.get_note_statistics()
                    self.tei_ner_writer_params.tnw_test_note_entity_list = []
                    with col1_note:
                        st.subheader("Tagged Entites:")
                        for entity in sorted(mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]):
                            if entity in note_statistics.keys():
                                if st.checkbox(
                                    "Show Entity " + entity + " (" + str(note_statistics[entity][0]) + ")",
                                    True,
                                    key="tnw" + entity + "note",
                                ):
                                    self.tei_ner_writer_params.tnw_test_note_entity_list.append(entity)
                        st.subheader("Display Options:")
                        tnw_test_note_show_entity_name = st.checkbox(
                            "Display Entity names",
                            False,
                            key="tnw_display_entity_names_note",
                        )
                        st.subheader("Legend: ")
                        index = 0
                        for entity in sorted(mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]):
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
                                self.tei_ner_writer_params.tnw_test_note_entity_list,
                                sorted(mapping[self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]),
                                show_entity_names=tnw_test_note_show_entity_name,
                            )
                        )

    def show(self):
        st.latex("\\text{\Huge{TEI NER Prediction Writer Mapping}}")
        col1, col2 = st.columns(2)
        with col1:
            self.show_tnws()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
