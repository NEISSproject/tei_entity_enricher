import streamlit as st
import tei_entity_enricher.util.tei_parser as tp
import json
import os
from tei_entity_enricher.util.helper import (
    get_listoutput,
    transform_arbitrary_text_to_markdown,
)
from tei_entity_enricher.util.components import editable_single_column_table
from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
)
import tei_entity_enricher.menu.tei_ner_gb as gb


class TEIReader:
    def __init__(self, state, show_menu=True):
        self.state = state

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
            self.tng = gb.TEINERGroundtruthBuilder(state, show_menu=False)
            self.show()

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
            # st.success(config[tr_config_attr_name]+' saved.')

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
            self.state.tr_test_selected_config_name = None
            st.experimental_rerun()

    def show_editable_exclude_tags(self, excl_list, mode, name):
        st.markdown("Define Tags to Exclude from the text which should be considered.")
        return editable_single_column_table(entry_list=excl_list, key="tr_excl" + mode + name, head="Exclude")

    def show_editable_note_tags(self, note_list, mode, name):
        st.markdown("Define Tags that contain notes.")
        return editable_single_column_table(entry_list=note_list, key="tr_note" + mode + name, head="Note tags")

    def reset_tr_edit_states(self):
        self.state.tr_exclude_list = None
        self.state.tr_note_tags = None
        self.state.tr_name = None

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
            if self.state.tr_mode != mode:
                self.reset_tr_edit_states()
            self.state.tr_mode = mode
            tr_config_dict = {}
            init_use_notes = True
            if mode in [self.tr_config_mode_dupl, self.tr_config_mode_edit]:
                if self.tr_config_mode_dupl == mode:
                    options = list(self.configdict.keys())
                else:
                    options = self.editable_config_names
                selected_config_name = st.selectbox(f"Select a config to {mode}!", options, key=mode)
                if self.state.tr_sel_config_name != selected_config_name:
                    self.reset_tr_edit_states()
                self.state.tr_sel_config_name = selected_config_name
                tr_config_dict = self.configdict[selected_config_name].copy()
                init_use_notes = tr_config_dict[self.tr_config_attr_use_notes]
                if mode == self.tr_config_mode_dupl:
                    tr_config_dict[self.tr_config_attr_name] = ""
            if mode == self.tr_config_mode_add:
                tr_config_dict[self.tr_config_attr_excl_tags] = []
                tr_config_dict[self.tr_config_attr_note_tags] = []
            if mode in [self.tr_config_mode_dupl, self.tr_config_mode_add]:
                self.state.tr_name = st.text_input("New TEI Reader Config Name:", self.state.tr_name or "")
                if self.state.tr_name:
                    tr_config_dict[self.tr_config_attr_name] = self.state.tr_name
            init_exclude_list = tr_config_dict[self.tr_config_attr_excl_tags]

            self.state.tr_exclude_list = self.show_editable_exclude_tags(
                self.state.tr_exclude_list if self.state.tr_exclude_list else init_exclude_list,
                mode,
                tr_config_dict[self.tr_config_attr_name] if self.tr_config_attr_name in tr_config_dict.keys() else "",
            )
            # st.write('Tags to exclude: '+ self.get_listoutput(self.state.tr_exclude_list))
            init_note_tags = tr_config_dict[self.tr_config_attr_note_tags]
            use_notes = st.checkbox("Tag Notes", init_use_notes)
            tr_config_dict[self.tr_config_attr_use_notes] = use_notes
            if tr_config_dict[self.tr_config_attr_use_notes]:
                self.state.tr_note_tags = self.show_editable_note_tags(
                    self.state.tr_note_tags if self.state.tr_note_tags else init_note_tags,
                    mode,
                    tr_config_dict[self.tr_config_attr_name]
                    if self.tr_config_attr_name in tr_config_dict.keys()
                    else "",
                )
            if st.button("Save TEI Reader Config", key=mode):
                tr_config_dict[self.tr_config_attr_excl_tags] = self.state.tr_exclude_list
                tr_config_dict[self.tr_config_attr_note_tags] = (
                    self.state.tr_note_tags
                    if self.state.tr_note_tags and tr_config_dict[self.tr_config_attr_use_notes]
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
        selected_config_name = st.selectbox("Select a config to delete!", self.editable_config_names)
        if st.button("Delete Selected Config"):
            self.validate_and_delete_config(self.configdict[selected_config_name])

    def show_edit_environment(self):
        tr_config_definer = st.beta_expander("Add or edit existing Config", expanded=False)
        with tr_config_definer:
            options = {
                "Add TEI Reader Config": self.tei_reader_add,
                "Duplicate TEI Reader Config": self.tei_reader_dupl,
                "Edit TEI Reader Config": self.tei_reader_edit,
                "Delete TEI Reader Config": self.teireaderdel,
            }
            self.state.tr_edit_options = st.radio(
                "Edit Options",
                tuple(options.keys()),
                tuple(options.keys()).index(self.state.tr_edit_options) if self.state.tr_edit_options else 0,
            )
            options[self.state.tr_edit_options]()

    def show_test_environment(self):
        tr_test_expander = st.beta_expander("Test TEI Reader Config", expanded=False)
        with tr_test_expander:
            self.state.tr_test_selected_config_name = st.selectbox(
                "Select a TEI Reader Config to test!",
                list(self.configdict.keys()),
                index=list(self.configdict.keys()).index(self.state.tr_test_selected_config_name)
                if self.state.tr_test_selected_config_name
                else 0,
                key="tr_test",
            )
            config = self.configdict[self.state.tr_test_selected_config_name]
            self.state.teifile = st.text_input("Choose a TEI File:", self.state.teifile or "", key="tr_test_tei_file")
            if self.state.teifile:
                tei = tp.TEIFile(self.state.teifile, config)
                st.subheader("Text Content:")
                st.markdown(transform_arbitrary_text_to_markdown(tei.get_text()))
                if config[self.tr_config_attr_use_notes]:
                    st.subheader("Note Content:")
                    st.markdown(transform_arbitrary_text_to_markdown(tei.get_notes()))

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
            st.markdown(' ') #only for layouting reasons (placeholder)

    def show(self):
        st.latex("\\text{\Huge{TEI Reader Config}}")
        col1, col2 = st.beta_columns(2)
        with col1:
            self.show_configs()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
