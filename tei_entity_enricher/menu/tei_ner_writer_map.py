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
    menu_entity_definition,
    menu_TEI_reader_config,
    menu_TEI_write_mapping,
)
from tei_entity_enricher.util.components import (
    editable_multi_column_table,
    editable_single_column_table,
    small_file_selector,
)
import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.util.tei_parser as tp


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
        self.check_one_time_attributes()

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
            self.check_rerun_messages()

    def check_rerun_messages(self):
        if "tnw_rerun_save_message" in st.session_state and st.session_state.tnw_rerun_save_message is not None:
            st.session_state.tnw_save_message=st.session_state.tnw_rerun_save_message
            st.session_state.tnw_rerun_save_message = None
            st.experimental_rerun()

    def check_one_time_attributes(self):
        if "tnw_save_message" in st.session_state and st.session_state.tnw_save_message is not None:
            self.tnw_save_message = st.session_state.tnw_save_message
            st.session_state.tnw_save_message = None
        else:
            self.tnw_save_message = None

        if "tnw_reload_aggrids" in st.session_state and st.session_state.tnw_reload_aggrids == True:
            self.tnw_reload_aggrids = True
            st.session_state.tnw_reload_aggrids = False
        else:
            self.tnw_reload_aggrids = False

    def validate_mapping_for_saving(self, mapping, mode):
        val = True
        if (
            self.tnw_attr_name not in mapping.keys()
            or mapping[self.tnw_attr_name] is None
            or mapping[self.tnw_attr_name] == ""
        ):
            val = False
            if self.tnw_save_message is None:
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
            if self.tnw_save_message is None:
                st.error(f"Choose another name. There is already a mapping with name {mapping[self.tnw_attr_name]}!")
        if len(mapping[self.tnw_attr_fixed_tags]) > 0:
            for fix_tag in mapping[self.tnw_attr_fixed_tags]:
                if " " in fix_tag:
                    val = False
                    if self.tnw_save_message is None:
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
                    if self.tnw_save_message is None:
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
                        if self.tnw_save_message is None:
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
                        if self.tnw_save_message is None:
                            st.error(
                                f"For the entity {entity} and tag {mapping[self.tnw_attr_entity_dict][entity][0]} you defined the attribute {attribute} without a value for it. This is not allowed."
                            )
                    elif " " in attribute:
                        val = False
                        if self.tnw_save_message is None:
                            st.error(
                                f"For the entity {entity} and tag {mapping[self.tnw_attr_entity_dict][entity][0]} you defined an attribute name ({attribute}) containing a space character. This is not allowed!"
                            )
                    elif " " in mapping[self.tnw_attr_entity_dict][entity][1][attribute]:
                        val = False
                        if self.tnw_save_message is None:
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
            if self.tnw_save_message is None:
                st.error(f"Please define at least one mapping of an entity to a tag. Otherwise there is nothing to save.")

        return val

    def validate_mapping_for_delete(self, mapping):
        val = True
        return val

    def show_editable_fixed_tags(self, fixed_list, key):
        st.markdown("Define tags in which no entities should be written.")
        return editable_single_column_table(
            entry_list=fixed_list, key=key, head="Fixed Tags", reload=self.tnw_reload_aggrids
        )

    def show_editable_attr_value_def(self, attr_value_dict, name):
        st.markdown("Define optionally attributes with values which have to be set for this tag!")
        entry_dict = {"Attributes": [], "Values": []}
        for key in attr_value_dict.keys():
            entry_dict["Attributes"].append(key)
            entry_dict["Values"].append(attr_value_dict[key])
        answer = editable_multi_column_table(
            entry_dict, "tnw_attr_value" + name, openentrys=20, reload=self.tnw_reload_aggrids
        )
        returndict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in returndict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            returndict[answer["Attributes"][i]] = answer["Values"][i]
        return returndict

    def build_tnw_ntd_sel_key(self, mode):
        return (
            "tnw_ntd_sel_"
            + mode
            + ("" if mode == self.tnw_mode_add else st.session_state["tnw_sel_mapping_name_" + mode])
        )

    def build_tnw_fixed_tags_key(self, mode):
        return (
            "tnw_fixed_tags_"
            + mode
            + ("" if mode == self.tnw_mode_add else st.session_state["tnw_sel_mapping_name_" + mode])
        )

    def build_tnw_sel_edit_entity_key(self, mode):
        return (
            "tnw_ent_" + mode + ("" if mode == self.tnw_mode_add else st.session_state["tnw_sel_mapping_name_" + mode])
        )

    def show_editable_mapping_content(self, mode):
        if mode == self.tnw_mode_edit and len(self.editable_mapping_names) < 1:
            st.info(
                f"There are no self-defined {menu_TEI_write_mapping}s to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            tnw_mapping_dict = {}
            init_tnw_ntd_name = ""
            init_tnw_entity_dict = {}
            if mode in [self.tnw_mode_dupl, self.tnw_mode_edit]:

                def tnw_sel_mapping_name_change(mode):
                    st.session_state.tnw_reload_aggrids = True
                    if "tnw_entity_dict" in st.session_state:
                        del st.session_state["tnw_entity_dict"]

                if self.tnw_mode_dupl == mode:
                    options = list(self.mappingdict.keys())
                else:
                    options = self.editable_mapping_names
                st.selectbox(
                    label=f"Select a mapping to {mode}!",
                    options=options,
                    key="tnw_sel_mapping_name_" + mode,
                    on_change=tnw_sel_mapping_name_change,
                    args=(mode,),
                )
                tnw_mapping_dict = self.mappingdict[st.session_state["tnw_sel_mapping_name_" + mode]].copy()
                init_tnw_ntd_name = tnw_mapping_dict[self.tnw_attr_ntd][self.ntd.ntd_attr_name]
                init_tnw_entity_dict = tnw_mapping_dict[self.tnw_attr_entity_dict]
                if mode == self.tnw_mode_dupl:
                    tnw_mapping_dict[self.tnw_attr_name] = ""
            if mode == self.tnw_mode_add:
                tnw_mapping_dict[self.tnw_attr_ntd] = {}
                tnw_mapping_dict[self.tnw_attr_entity_dict] = {}
                tnw_mapping_dict[self.tnw_attr_fixed_tags] = []
            if mode in [self.tnw_mode_dupl, self.tnw_mode_add]:
                st.text_input(f"New {menu_TEI_write_mapping} Name:", key="tnw_name_" + mode)
                tnw_mapping_dict[self.tnw_attr_name] = st.session_state["tnw_name_" + mode]

            def tnw_ntd_change_trigger(mode):
                st.session_state.tnm_reload_aggrids = True
                if self.build_tnw_sel_edit_entity_key(mode) in st.session_state:
                    del st.session_state[self.build_tnw_sel_edit_entity_key(mode)]
                if "tnw_entity_dict" in st.session_state:
                    del st.session_state["tnw_entity_dict"]

            st.selectbox(
                label=f"Corresponding {menu_entity_definition}",
                options=list(self.ntd.defdict.keys()),
                index=list(self.ntd.defdict.keys()).index(init_tnw_ntd_name)
                if init_tnw_ntd_name is not None and init_tnw_ntd_name != ""
                else 0,
                key=self.build_tnw_ntd_sel_key(mode),
                on_change=tnw_ntd_change_trigger,
                args=(mode,),
            )
            init_fixed_list = tnw_mapping_dict[self.tnw_attr_fixed_tags]
            tnw_mapping_dict[self.tnw_attr_fixed_tags] = self.show_editable_fixed_tags(
                fixed_list=init_fixed_list,
                key=self.build_tnw_fixed_tags_key(mode),
            )
            if self.build_tnw_ntd_sel_key(mode) in st.session_state:
                options = self.ntd.defdict[st.session_state[self.build_tnw_ntd_sel_key(mode)]][
                    self.ntd.ntd_attr_entitylist
                ]
                st.selectbox(
                    label="Define mapping for entity:",
                    options=options,
                    key=self.build_tnw_sel_edit_entity_key(mode),
                )
                st.session_state.tnw_entity_dict = self.edit_entity(
                    mode,
                    st.session_state[self.build_tnw_sel_edit_entity_key(mode)],
                    st.session_state.tnw_entity_dict if "tnw_entity_dict" in st.session_state else init_tnw_entity_dict,
                )

            tnw_mapping_dict[self.tnw_attr_ntd] = self.ntd.defdict[st.session_state[self.build_tnw_ntd_sel_key(mode)]]
            tnw_mapping_dict[self.tnw_attr_entity_dict] = st.session_state.tnw_entity_dict.copy()

            def save_mapping(mapping, mode):
                mapping[self.tnw_attr_template] = False
                with open(
                    os.path.join(
                        self.tnw_Folder,
                        mapping[self.tnw_attr_name].replace(" ", "_") + ".json",
                    ),
                    "w+",
                ) as f:
                    json.dump(mapping, f)
                for key in st.session_state:
                    if (
                        key.startswith("tnw_ntd_sel_" + mode)
                        or key.startswith("tnw_ent_" + mode)
                        or key.startswith("tnw_fixed_tags_" + mode)
                        or key.startswith("tnw_name_" + mode)
                    ):
                        del st.session_state[key]
                st.session_state.tnw_save_message = (
                    f"{menu_TEI_write_mapping} {mapping[self.tnw_attr_name]} succesfully saved!"
                )
                st.session_state.tnw_reload_aggrids = True
                del st.session_state["tnw_entity_dict"]

            if self.tnw_save_message is not None:
                st.success(self.tnw_save_message)

            if self.validate_mapping_for_saving(tnw_mapping_dict, mode):
                st.button(
                    f"Save {menu_TEI_write_mapping}",
                    key="tnm_save_" + mode,
                    on_click=save_mapping,
                    args=(
                        tnw_mapping_dict,
                        mode,
                    ),
                )

    def edit_entity(self, mode, tnw_edit_entity, cur_entity_dict):
        if tnw_edit_entity not in cur_entity_dict.keys():
            cur_entity_dict[tnw_edit_entity] = [None, {}]
        mapping_entry = cur_entity_dict[tnw_edit_entity]
        mapping_entry[0] = st.text_input(
            "Tag",
            mapping_entry[0] or "",
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
        def delete_mapping(mapping):
            os.remove(
                os.path.join(
                    self.tnw_Folder,
                    mapping[self.tnw_attr_name].replace(" ", "_") + ".json",
                )
            )
            st.session_state.tnw_rerun_save_message = (
                f"{menu_TEI_write_mapping} {mapping[self.tnw_attr_name]} succesfully deleted!"
            )
            st.session_state.tnw_reload_aggrids = True
            del st.session_state["tnw_sel_wri_del_name"]
            if (
                "tnw_sel_details_name" in st.session_state
                and mapping[self.tnw_attr_name] == st.session_state.tnw_sel_details_name
            ):
                del st.session_state["tnw_sel_details_name"]
            for mode in [self.tnw_mode_dupl, self.tnw_mode_edit]:
                if "tnw_sel_mapping_name_" + mode in st.session_state:
                    del st.session_state["tnw_sel_mapping_name_" + mode]
            if "tnw_tnw_test" in st.session_state:
                del st.session_state["tnw_tnw_test"]

        if len(self.editable_mapping_names) > 0:
            st.selectbox(
                label="Select a mapping to delete!",
                options=self.editable_mapping_names,
                key="tnw_sel_wri_del_name",
            )
            if self.validate_mapping_for_delete(self.mappingdict[st.session_state.tnw_sel_wri_del_name]):
                st.button(
                    "Delete Selected Mapping",
                    on_click=delete_mapping,
                    args=(self.mappingdict[st.session_state.tnw_sel_wri_del_name],),
                )
        else:
            st.info(f"There are no self-defined {menu_TEI_write_mapping}s to delete!")
        if self.tnw_save_message is not None:
            st.success(self.tnw_save_message)

    def show_edit_environment(self):
        tnw_definer = st.expander(f"Add or edit existing {menu_TEI_write_mapping}s", expanded=False)
        with tnw_definer:

            def change_edit_option_trigger():
                st.session_state.tnw_reload_aggrids = True
                if "tnw_entity_dict" in st.session_state:
                    del st.session_state["tnw_entity_dict"]

            if self.tnw_save_message is not None:
                st.success(self.tnw_save_message)

            options = {
                f"Add {menu_TEI_write_mapping}": self.tei_ner_map_add,
                f"Duplicate {menu_TEI_write_mapping}": self.tei_ner_map_dupl,
                f"Edit {menu_TEI_write_mapping}": self.tei_ner_map_edit,
                f"Delete {menu_TEI_write_mapping}": self.tei_ner_map_del,
            }
            st.radio(
                label="Edit Options",
                options=tuple(options.keys()),
                key="tnw_choose_edit_option",
                on_change=change_edit_option_trigger,
            )
            options[st.session_state.tnw_choose_edit_option]()

    def build_tnw_tablestring(self):
        tablestring = f"Name | {menu_entity_definition} | Fixed Tags | Template \n -----|-------|-------|-------"
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
        tnw_show = st.expander(f"Existing {menu_TEI_write_mapping}s", expanded=True)
        with tnw_show:
            st.markdown(self.build_tnw_tablestring())
            st.selectbox(
                label=f"Choose a mapping for displaying its details:",
                options=list(self.mappingdict.keys()),
                key="tnw_sel_details_name",
            )
            if "tnw_sel_details_name" in st.session_state:
                cur_sel_mapping = self.mappingdict[st.session_state.tnw_sel_details_name]
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
        tnw_test_expander = st.expander(f"Test {menu_TEI_write_mapping}", expanded=False)
        with tnw_test_expander:
            # self.tei_ner_writer_params.tnw_test_selected_config_name
            st.selectbox(
                label=f"Select a {menu_TEI_reader_config} for the mapping test!",
                options=list(self.tr.configdict.keys()),
                key="tnw_tr_test",
            )
            config = self.tr.configdict[st.session_state.tnw_tr_test]
            # self.tei_ner_writer_params.tnw_test_selected_mapping_name
            st.selectbox(
                label=f"Select a {menu_TEI_write_mapping} to test!",
                options=list(self.mappingdict.keys()),
                key="tnw_tnw_test",
            )
            mapping = self.mappingdict[st.session_state.tnw_tnw_test]
            # self.tei_ner_writer_params.tnw_teifile
            small_file_selector(
                label="Choose a TEI-File",
                key="tnw_test_TEI_file",
                help=f"Choose a TEI file for testing the chosen {menu_TEI_write_mapping}",
            )
            if st.button(
                f"Test {menu_TEI_write_mapping}",
                key="tnw_Button_Test",
                help=f"Test {menu_TEI_write_mapping} on the chosen {menu_TEI_reader_config} and TEI-File.",
            ):
                if os.path.isfile(st.session_state.tnw_test_TEI_file):
                    st.session_state.tnw_last_test_dict = {
                        "teifile": st.session_state.tnw_test_TEI_file,
                        "tr": config.copy(),
                        "tnw": mapping.copy(),
                    }
                else:
                    st.error(f"The chosen path {st.session_state.tnw_test_TEI_file} is not a file!")
                    st.session_state.tnw_last_test_dict = {}
            if "tnw_last_test_dict" in st.session_state and len(st.session_state.tnw_last_test_dict.keys()) > 0:
                tei = tp.TEIFile(
                    st.session_state.tnw_last_test_dict["teifile"],
                    st.session_state.tnw_last_test_dict["tr"],
                    entity_dict=st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_entity_dict],
                )
                col1, col2 = st.columns([0.2, 0.8])
                statistics = tei.get_statistics()
                st.session_state.tnw_test_entity_list = []
                with col1:
                    st.subheader("Tagged Entites:")
                    for entity in sorted(
                        st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]
                    ):
                        if entity in statistics.keys():
                            if st.checkbox(
                                "Show Entity " + entity + " (" + str(statistics[entity][0]) + ")",
                                True,
                                key="tnw" + entity + "text",
                            ):
                                st.session_state.tnw_test_entity_list.append(entity)
                    st.subheader("Display Options:")
                    tnw_test_show_entity_name = st.checkbox(
                        "Display Entity names", False, key="tnw_display_entity_names"
                    )
                    st.subheader("Legend:")
                    index = 0
                    for entity in sorted(
                        st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]
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
                            st.session_state.tnw_test_entity_list,
                            sorted(
                                st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_ntd][
                                    self.ntd.ntd_attr_entitylist
                                ]
                            ),
                            show_entity_names=tnw_test_show_entity_name,
                        )
                    )
                if config[self.tr.tr_config_attr_use_notes]:
                    col1_note, col2_note = st.columns([0.2, 0.8])
                    note_statistics = tei.get_note_statistics()
                    st.session_state.tnw_test_note_entity_list = []
                    with col1_note:
                        st.subheader("Tagged Entites:")
                        for entity in sorted(
                            st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]
                        ):
                            if entity in note_statistics.keys():
                                if st.checkbox(
                                    "Show Entity " + entity + " (" + str(note_statistics[entity][0]) + ")",
                                    True,
                                    key="tnw" + entity + "note",
                                ):
                                    st.session_state.tnw_test_note_entity_list.append(entity)
                        st.subheader("Display Options:")
                        tnw_test_note_show_entity_name = st.checkbox(
                            "Display Entity names",
                            False,
                            key="tnw_display_entity_names_note",
                        )
                        st.subheader("Legend: ")
                        index = 0
                        for entity in sorted(
                            st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_ntd][self.ntd.ntd_attr_entitylist]
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
                                st.session_state.tnw_test_note_entity_list,
                                sorted(
                                    st.session_state.tnw_last_test_dict["tnw"][self.tnw_attr_ntd][
                                        self.ntd.ntd_attr_entitylist
                                    ]
                                ),
                                show_entity_names=tnw_test_note_show_entity_name,
                            )
                        )

    def show(self):
        st.latex("\\text{\Huge{" + menu_TEI_write_mapping + "}}")
        col1, col2 = st.columns(2)
        with col1:
            self.show_tnws()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
