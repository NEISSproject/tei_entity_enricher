import streamlit as st
import tei_entity_enricher.util.tei_parser as tp
import json
import os
from tei_entity_enricher.util.helper import (
    get_listoutput,
    transform_arbitrary_text_to_latex,
)
from tei_entity_enricher.util.components import (
    editable_single_column_table,
    small_file_selector,
    radio_widget,
    selectbox_widget,
    text_input_widget,
)
from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
)
import tei_entity_enricher.menu.tei_ner_gb as gb
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List,Dict


@dataclass
@dataclass_json
class TEINERReaderParams:
    tr_edit_options: str = None
    tr_del_config_name: str = None
    tr_test_selected_config_name: str = None
    tr_teifile: str = None
    tr_last_test_dict: Dict = None
    tr_mode: str = None
    tr_sel_config_name: str = None
    tr_name: str = None
    tr_exclude_list: List = None
    tr_note_tags: List = None


@st.cache(allow_output_mutation=True)
def get_params() -> TEINERReaderParams:
    return TEINERReaderParams()


class TEIReader:
    def __init__(self,show_menu=True):
        self.config_Folder = "TR_Configs"
        self.template_config_Folder = os.path.join(module_path, "templates", self.config_Folder)
        self.config_Folder = os.path.join(local_save_path, self.config_Folder)
        self.tr_config_attr_name = "name"
        self.tr_config_attr_excl_tags = "exclude_tags"
        self.tr_config_attr_use_notes = "use_notes"
        self.tr_config_attr_note_tags = "note_tags"
        self.tr_config_attr_template = "template"
        self.tr_config_mode_add = "add"
        self.tr_config_mode_dupl = "duplicate"
        self.tr_config_mode_edit = "edit"

        self.configslist = []
        makedir_if_necessary(self.config_Folder)
        makedir_if_necessary(self.template_config_Folder)

        for configFile in sorted(os.listdir(self.template_config_Folder)):
            if configFile.endswith("json"):
                with open(os.path.join(self.template_config_Folder, configFile)) as f:
                    self.configslist.append(json.load(f))
        for configFile in sorted(os.listdir(self.config_Folder)):
            if configFile.endswith("json"):
                with open(os.path.join(self.config_Folder, configFile)) as f:
                    self.configslist.append(json.load(f))

        self.configdict = {}
        self.editable_config_names = []
        for config in self.configslist:
            self.configdict[config[self.tr_config_attr_name]] = config
            if not config[self.tr_config_attr_template]:
                self.editable_config_names.append(config[self.tr_config_attr_name])
        if show_menu:
            self.tng = gb.TEINERGroundtruthBuilder(show_menu=False)
            self.show()

    @property
    def tei_ner_reader_params(self) -> TEINERReaderParams:
        return get_params()

    def validate_and_saving_config(self, config, mode):
        val = True
        if (
            self.tr_config_attr_name not in config.keys()
            or config[self.tr_config_attr_name] is None
            or config[self.tr_config_attr_name] == ""
        ):
            val = False
            st.error("Please define a name for the config before saving!")
        elif (
            os.path.isfile(
                os.path.join(
                    self.config_Folder,
                    config[self.tr_config_attr_name].replace(" ", "_") + ".json",
                )
            )
            and mode != self.tr_config_mode_edit
        ):
            val = False
            st.error(f"Choose another name. There is already a config with name {config[self.tr_config_attr_name]}!")
        if len(config[self.tr_config_attr_excl_tags]) > 0:
            for excl_tag in config[self.tr_config_attr_excl_tags]:
                if " " in excl_tag:
                    val = False
                    st.error(
                        f"You defined an exclude tag ({excl_tag}) containing a space character. This is not allowed!"
                    )
        if config[self.tr_config_attr_use_notes] and len(config[self.tr_config_attr_note_tags]) < 1:
            val = False
            st.error(
                "You setted the checkbox that notes should be tagged but you did not define which tags contain notes! Please define at least one tag that contain notes."
            )
        elif config[self.tr_config_attr_use_notes]:
            for note_tag in config[self.tr_config_attr_note_tags]:
                if " " in note_tag:
                    val = False
                    st.error(f"You defined an note tag ({note_tag}) containing a space character. This is not allowed!")
        if (
            config[self.tr_config_attr_use_notes]
            and len(set(config[self.tr_config_attr_note_tags]).intersection(config[self.tr_config_attr_excl_tags])) > 0
        ):
            val = False
            if len(set(config[self.tr_config_attr_note_tags]).intersection(config[self.tr_config_attr_excl_tags])) > 1:
                warntext = f"Tags can either be excluded or marked as note tags. Please define for the tags {get_listoutput(list(set(config[self.tr_config_attr_note_tags]).intersection(config[self.tr_config_attr_excl_tags])))} whether they should be excluded or considered as notes."
            else:
                warntext = f"Tags can either be excluded or marked as note tags. Please define for the tag {get_listoutput(list(set(config[self.tr_config_attr_note_tags]).intersection(config[self.tr_config_attr_excl_tags])))} whether it should be excluded or considered as a note."
            st.error(warntext)
        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tr][self.tr_config_attr_name] == config[self.tr_config_attr_name]:
                val = False
                st.error(
                    f"To edit the TEI Reader Config {config[self.tr_config_attr_name]} is not allowed because it is already used in the TEI NER Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the config to the groundtruth."
                )

        if val:
            config[self.tr_config_attr_template] = False
            with open(
                os.path.join(
                    self.config_Folder,
                    config[self.tr_config_attr_name].replace(" ", "_") + ".json",
                ),
                "w+",
            ) as f:
                json.dump(config, f)
            self.reset_tr_edit_states()
            st.experimental_rerun()

    def validate_and_delete_config(self, config):
        val = True
        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tr][self.tr_config_attr_name] == config[self.tr_config_attr_name]:
                val = False
                st.error(
                    f"To delete the TEI Reader Config {config[self.tr_config_attr_name]} is not allowed because it is already used in the TEI NER Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the config to the groundtruth."
                )

        if val:
            os.remove(
                os.path.join(
                    self.config_Folder,
                    config[self.tr_config_attr_name].replace(" ", "_") + ".json",
                )
            )
            self.reset_tr_edit_states()
            self.tei_ner_reader_params.tr_sel_config_name = None
            if config[self.tr_config_attr_name] == self.tei_ner_reader_params.tr_test_selected_config_name:
                self.tei_ner_reader_params.tr_test_selected_config_name = None
            if config[self.tr_config_attr_name] == self.tei_ner_reader_params.tr_sel_config_name:
                self.tei_ner_reader_params.tr_sel_config_name = None
            self.tei_ner_reader_params.tr_del_config_name = None
            st.experimental_rerun()

    def show_editable_exclude_tags(self, excl_list, mode, name, dupl_name):
        st.markdown("Define Tags to Exclude from the text which should be considered.")
        return editable_single_column_table(
            entry_list=excl_list, key="tr_excl" + mode + name + dupl_name, head="Exclude"
        )

    def show_editable_note_tags(self, note_list, mode, name, dupl_name):
        st.markdown("Define Tags that contain notes.")
        return editable_single_column_table(
            entry_list=note_list, key="tr_note" + mode + name + dupl_name, head="Note tags"
        )

    def reset_tr_edit_states(self):
        self.tei_ner_reader_params.tr_exclude_list = None
        self.tei_ner_reader_params.tr_note_tags = None
        self.tei_ner_reader_params.tr_name = None


    def are_configs_equal(self, config1, config2):
        for key in config1.keys():
            if config1[key] != config2[key]:
                return False
        return True

    def show_editable_config_content(self, mode):
        if mode == self.tr_config_mode_edit and len(self.editable_config_names) < 1:
            st.info(
                "There are no self-defined TEI Reader Configs to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            if self.tei_ner_reader_params.tr_mode != mode:
                self.reset_tr_edit_states()
                self.tei_ner_reader_params.tr_sel_config_name = None
            self.tei_ner_reader_params.tr_mode = mode
            tr_config_dict = {}
            init_use_notes = True
            if mode in [self.tr_config_mode_dupl, self.tr_config_mode_edit]:
                if self.tr_config_mode_dupl == mode:
                    options = list(self.configdict.keys())
                else:
                    options = self.editable_config_names
                    if self.tei_ner_reader_params.tr_sel_config_name not in self.editable_config_names:
                        self.tei_ner_reader_params.tr_sel_config_name= None
                selected_config_name = selectbox_widget(
                    f"Select a config to {mode}!",
                    options,
                    key=mode,
                    index=options.index(self.tei_ner_reader_params.tr_sel_config_name)
                    if self.tei_ner_reader_params.tr_sel_config_name
                    else 0,
                )
                if self.tei_ner_reader_params.tr_sel_config_name != selected_config_name:
                    self.reset_tr_edit_states()
                self.tei_ner_reader_params.tr_sel_config_name = selected_config_name
                tr_config_dict = self.configdict[selected_config_name].copy()
                init_use_notes = tr_config_dict[self.tr_config_attr_use_notes]
                if mode == self.tr_config_mode_dupl:
                    tr_config_dict[self.tr_config_attr_name] = ""
            else:
                selected_config_name = ""
            if mode == self.tr_config_mode_add:
                tr_config_dict[self.tr_config_attr_excl_tags] = []
                tr_config_dict[self.tr_config_attr_note_tags] = []
            if mode in [self.tr_config_mode_dupl, self.tr_config_mode_add]:
                self.tei_ner_reader_params.tr_name = text_input_widget("New TEI Reader Config Name:", self.tei_ner_reader_params.tr_name or "")
                if self.tei_ner_reader_params.tr_name:
                    tr_config_dict[self.tr_config_attr_name] = self.tei_ner_reader_params.tr_name
            init_exclude_list = tr_config_dict[self.tr_config_attr_excl_tags]

            self.tei_ner_reader_params.tr_exclude_list = self.show_editable_exclude_tags(
                self.tei_ner_reader_params.tr_exclude_list if self.tei_ner_reader_params.tr_exclude_list else init_exclude_list,
                mode,
                tr_config_dict[self.tr_config_attr_name] if self.tr_config_attr_name in tr_config_dict.keys() else "",
                selected_config_name,
            )
            init_note_tags = tr_config_dict[self.tr_config_attr_note_tags]
            use_notes = st.checkbox("Tag Notes", init_use_notes)
            tr_config_dict[self.tr_config_attr_use_notes] = use_notes
            if tr_config_dict[self.tr_config_attr_use_notes]:
                self.tei_ner_reader_params.tr_note_tags = self.show_editable_note_tags(
                    self.tei_ner_reader_params.tr_note_tags if self.tei_ner_reader_params.tr_note_tags else init_note_tags,
                    mode,
                    tr_config_dict[self.tr_config_attr_name]
                    if self.tr_config_attr_name in tr_config_dict.keys()
                    else "",
                    selected_config_name,
                )
            if st.button("Save TEI Reader Config", key=mode):
                tr_config_dict[self.tr_config_attr_excl_tags] = self.tei_ner_reader_params.tr_exclude_list
                tr_config_dict[self.tr_config_attr_note_tags] = (
                    self.tei_ner_reader_params.tr_note_tags
                    if self.tei_ner_reader_params.tr_note_tags and tr_config_dict[self.tr_config_attr_use_notes]
                    else []
                )
                self.validate_and_saving_config(tr_config_dict, mode)

    def tei_reader_add(self):
        self.show_editable_config_content(self.tr_config_mode_add)

    def tei_reader_dupl(self):
        self.show_editable_config_content(self.tr_config_mode_dupl)

    def tei_reader_edit(self):
        self.show_editable_config_content(self.tr_config_mode_edit)

    def teireaderdel(self):
        if len(self.editable_config_names) > 0:
            self.tei_ner_reader_params.tr_del_config_name = selectbox_widget(
                "Select a config to delete!",
                self.editable_config_names,
                index=self.editable_config_names.index(self.tei_ner_reader_params.tr_del_config_name)
                if self.tei_ner_reader_params.tr_del_config_name
                else 0,
            )
            if st.button("Delete Selected Config"):
                self.validate_and_delete_config(self.configdict[self.tei_ner_reader_params.tr_del_config_name])
        else:
            st.info("There are no self-defined TEI Read NER Reader Configs to delete!")

    def show_edit_environment(self):
        tr_config_definer = st.beta_expander("Add or edit existing Config", expanded=False)
        with tr_config_definer:
            options = {
                "Add TEI Reader Config": self.tei_reader_add,
                "Duplicate TEI Reader Config": self.tei_reader_dupl,
                "Edit TEI Reader Config": self.tei_reader_edit,
                "Delete TEI Reader Config": self.teireaderdel,
            }
            self.tei_ner_reader_params.tr_edit_options = radio_widget(
                "Edit Options",
                tuple(options.keys()),
                tuple(options.keys()).index(self.tei_ner_reader_params.tr_edit_options)
                if self.tei_ner_reader_params.tr_edit_options
                else 0,
            )
            options[self.tei_ner_reader_params.tr_edit_options]()

    def show_test_environment(self):
        tr_test_expander = st.beta_expander("Test TEI Reader Config", expanded=False)
        with tr_test_expander:
            self.tei_ner_reader_params.tr_test_selected_config_name = selectbox_widget(
                "Select a TEI Reader Config to test!",
                list(self.configdict.keys()),
                index=list(self.configdict.keys()).index(self.tei_ner_reader_params.tr_test_selected_config_name)
                if self.tei_ner_reader_params.tr_test_selected_config_name
                else 0,
                key="tr_test",
            )
            config = self.configdict[self.tei_ner_reader_params.tr_test_selected_config_name]
            self.tei_ner_reader_params.tr_teifile = small_file_selector(
                label="Choose a TEI-File",
                value=self.tei_ner_reader_params.tr_teifile
                if self.tei_ner_reader_params.tr_teifile
                else local_save_path,
                key="tr_test_choose_tei",
                help="Choose a TEI file for testing the chosen TEI Reader Config",
            )
            if st.button(
                "Test TEI Reader Config",
                key="tr_Button_Test",
                help="Test TEI Reader Config on the chosen Config and TEI-File.",
            ):
                if os.path.isfile(self.tei_ner_reader_params.tr_teifile):
                    self.tei_ner_reader_params.tr_last_test_dict = {
                        "teifile": self.tei_ner_reader_params.tr_teifile,
                        "tr": config,
                    }
                else:
                    st.error(f"The chosen path {self.tei_ner_reader_params.tr_teifile} is not a file!")
                    self.tei_ner_reader_params.tr_last_test_dict = {}
            if (
                self.tei_ner_reader_params.tr_last_test_dict
                and len(self.tei_ner_reader_params.tr_last_test_dict.keys()) > 0
            ):
                tei = tp.TEIFile(
                    self.tei_ner_reader_params.tr_last_test_dict["teifile"],
                    self.tei_ner_reader_params.tr_last_test_dict["tr"],
                )
                st.subheader("Text Content:")
                st.write(transform_arbitrary_text_to_latex(tei.get_text()))
                if config[self.tr_config_attr_use_notes]:
                    st.subheader("Note Content:")
                    st.write(transform_arbitrary_text_to_latex(tei.get_notes()))

    def build_config_tablestring(self):
        tablestring = (
            "Name | Exclude Tags | Tagging Notes | Note Tags | Template \n -----|-------|-------|-------|-------"
        )
        for config in self.configslist:
            if config[self.tr_config_attr_use_notes]:
                use_notes = "yes"
            else:
                use_notes = "no"
            if config[self.tr_config_attr_template]:
                template = "yes"
            else:
                template = "no"
            tablestring += (
                "\n "
                + config[self.tr_config_attr_name]
                + " | "
                + get_listoutput(config[self.tr_config_attr_excl_tags])
                + " | "
                + use_notes
                + " | "
                + get_listoutput(config[self.tr_config_attr_note_tags])
                + " | "
                + template
            )
        return tablestring

    def show_configs(self):
        tr_show_configs = st.beta_expander("Existing TEI Reader Configs", expanded=True)
        with tr_show_configs:
            st.markdown(self.build_config_tablestring())
            st.markdown(" ")  # only for layouting reasons (placeholder)

    def show(self):
        st.latex("\\text{\Huge{TEI Reader Config}}")
        col1, col2 = st.beta_columns(2)
        with col1:
            self.show_configs()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
