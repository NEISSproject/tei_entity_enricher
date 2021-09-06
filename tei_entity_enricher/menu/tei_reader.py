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
)
from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
)
import tei_entity_enricher.menu.tei_ner_gb as gb


class TEIReader:
    def __init__(self, show_menu=True):
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
        if "tr_save_message" in st.session_state and st.session_state.tr_save_message is not None:
            self.tr_save_message = st.session_state.tr_save_message
            st.session_state.tr_save_message=None
        else:
            self.tr_save_message = None

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

    def validate_config_for_save(self, config, mode):
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
        return val

    def show_editable_exclude_tags(self, excl_list, key):
        st.markdown("Define Tags to Exclude from the text which should be considered.")
        return editable_single_column_table(
            entry_list=excl_list, key=key, head="Exclude"
        )

    def show_editable_note_tags(self, note_list, key):
        st.markdown("Define Tags that contain notes.")
        return editable_single_column_table(
            entry_list=note_list, key=key, head="Note tags"
        )

    def are_configs_equal(self, config1, config2):
        for key in config1.keys():
            if config1[key] != config2[key]:
                return False
        return True

    def build_excl_tag_key(self, mode):
        return (
            "tr_exclude_tags_"
            + mode
            + ("" if mode == self.tr_config_mode_add else st.session_state['tr_sel_config_name_'+mode])
        )

    def build_note_tag_key(self, mode):
        return (
            "tr_note_tags_"
            + mode
            + ("" if mode == self.tr_config_mode_add else st.session_state['tr_sel_config_name_'+mode])
        )

    def build_use_not_tag_key(self,mode):
        return (
            "use_tr_note_tags_"
            + mode
            + ("" if mode == self.tr_config_mode_add else st.session_state['tr_sel_config_name_'+mode])
        )


    def show_editable_config_content(self, mode):
        if mode == self.tr_config_mode_edit and len(self.editable_config_names) < 1:
            st.info(
                "There are no self-defined TEI Reader Configs to edit in the moment. If you want to edit a template you have to duplicate it."
            )
        else:
            tr_config_dict = {}
            init_use_notes = True
            if mode in [self.tr_config_mode_dupl, self.tr_config_mode_edit]:
                if self.tr_config_mode_dupl == mode:
                    options = list(self.configdict.keys())
                else:
                    options = self.editable_config_names
                st.selectbox(
                    label=f"Select a config to {mode}!",
                    options=options,
                    key='tr_sel_config_name_'+mode,
                    index=0,
                )
                tr_config_dict = self.configdict[st.session_state['tr_sel_config_name_'+mode]].copy()
                init_use_notes = tr_config_dict[self.tr_config_attr_use_notes]
                if mode == self.tr_config_mode_dupl:
                    tr_config_dict[self.tr_config_attr_name] = ""
            if mode == self.tr_config_mode_add:
                tr_config_dict[self.tr_config_attr_excl_tags] = []
                tr_config_dict[self.tr_config_attr_note_tags] = []
            if mode in [self.tr_config_mode_dupl, self.tr_config_mode_add]:
                st.text_input(
                    label="New TEI Reader Config Name:", key='tr_name_'+mode
                )
                tr_config_dict[self.tr_config_attr_name] = st.session_state['tr_name_'+mode]
            init_exclude_tags = tr_config_dict[self.tr_config_attr_excl_tags]
            #if self.build_excl_tag_key(mode) in st.session_state and st.session_state[self.build_excl_tag_key(mode)] is not None:
            #    st.write(st.session_state[self.build_excl_tag_key(mode)])

            tr_config_dict[self.tr_config_attr_excl_tags] = self.show_editable_exclude_tags(
                excl_list=init_exclude_tags,
                key=self.build_excl_tag_key(mode),
            )
            init_note_tags=tr_config_dict[self.tr_config_attr_note_tags]

            st.checkbox(label="Tag Notes",value= init_use_notes,key=self.build_use_not_tag_key(mode))
            tr_config_dict[self.tr_config_attr_use_notes] = st.session_state[self.build_use_not_tag_key(mode)]
            if tr_config_dict[self.tr_config_attr_use_notes]:
                tr_config_dict[self.tr_config_attr_note_tags] = self.show_editable_note_tags(
                    note_list=init_note_tags,
                    key=self.build_note_tag_key(mode),
                )
            def save_config(config):
                config[self.tr_config_attr_template] = False
                with open(
                    os.path.join(
                        self.config_Folder,
                        config[self.tr_config_attr_name].replace(" ", "_") + ".json",
                    ),
                    "w+",
                ) as f:
                    json.dump(config, f)
                if mode != self.tr_config_mode_edit:
                    st.session_state["tr_name_" + mode] = ""
                for key in st.session_state:
                    if key.startswith("tr_exclude_tags_" + mode) or key.startswith("tr_note_tags_" + mode) or key.startswith("use_tr_note_tags_" + mode):
                        del st.session_state[key]
                st.session_state.tr_save_message = f'TEI Reader Config {config[self.tr_config_attr_name]} succesfully saved!'
            if self.validate_config_for_save(tr_config_dict, mode):
                st.button("Save TEI Reader Config", key="tr_save_" + mode, on_click=save_config,args=(tr_config_dict,))


    def tei_reader_add(self):
        self.show_editable_config_content(self.tr_config_mode_add)

    def tei_reader_dupl(self):
        self.show_editable_config_content(self.tr_config_mode_dupl)

    def tei_reader_edit(self):
        self.show_editable_config_content(self.tr_config_mode_edit)

    def validate_config_for_delete(self, config):
        val = True
        for gt in self.tng.tnglist:
            if gt[self.tng.tng_attr_tr][self.tr_config_attr_name] == config[self.tr_config_attr_name]:
                val = False
                st.error(
                    f"To delete the TEI Reader Config {config[self.tr_config_attr_name]} is not allowed because it is already used in the TEI NER Groundtruth {gt[self.tng.tng_attr_name]}. If necessary, first remove the assignment of the config to the groundtruth."
                )
        return val

    def teireaderdel(self):
        def delete_config(config):
            os.remove(
                os.path.join(
                    self.config_Folder,
                    config[self.tr_config_attr_name].replace(" ", "_") + ".json",
                )
            )
            st.session_state.tr_save_message = f'TEI Reader Config {config[self.tr_config_attr_name]} succesfully deleted!'
            if (
                "tr_test_selected_config_name" in st.session_state
                and config[self.tr_config_attr_name] == st.session_state.tr_test_selected_config_name
            ):
                del st.session_state["tr_test_selected_config_name"]
            if "tr_sel_config_name" in st.session_state and config[self.tr_config_attr_name] == st.session_state.tr_sel_config_name:
                del st.session_state.tr_sel_config_name
            for mode in [self.tr_config_mode_dupl, self.tr_config_mode_edit]:
                if 'tr_sel_config_name_' + mode in st.session_state and st.session_state['tr_sel_config_name_'+mode]==config[self.tr_config_attr_name]:
                    del st.session_state['tr_sel_config_name_' + mode]
            del st.session_state["tr_del_config_name"]


        if len(self.editable_config_names) > 0:
            st.selectbox(
                label="Select a config to delete!",
                options=self.editable_config_names,
                key="tr_del_config_name",
            )
            if self.validate_config_for_delete(self.configdict[st.session_state.tr_del_config_name]):
                st.button(
                    "Delete Selected Config",
                    on_click=delete_config,
                    args=(self.configdict[st.session_state.tr_del_config_name],),
                )
        else:
            st.info("There are no self-defined TEI Read NER Reader Configs to delete!")

    def show_edit_environment(self):
        tr_config_definer = st.expander("Add or edit existing Config", expanded=False)
        with tr_config_definer:
            if self.tr_save_message is not None:
                st.success(self.tr_save_message)
                self.tr_save_message=None
            options = {
                "Add TEI Reader Config": self.tei_reader_add,
                "Duplicate TEI Reader Config": self.tei_reader_dupl,
                "Edit TEI Reader Config": self.tei_reader_edit,
                "Delete TEI Reader Config": self.teireaderdel,
            }
            st.radio(
                label="Edit Options",
                options=tuple(options.keys()),
                key="tr_edit_option",
            )
            options[st.session_state.tr_edit_option]()

    def show_test_environment(self):
        tr_test_expander = st.expander("Test TEI Reader Config", expanded=False)
        with tr_test_expander:
            st.selectbox(
                "Select a TEI Reader Config to test!",
                list(self.configdict.keys()),
                index=0,
                key="tr_test_selected_config_name",
            )
            config = self.configdict[st.session_state.tr_test_selected_config_name]
            if "tr_teifile" not in st.session_state:
                st.session_state.tr_teifile = local_save_path
            small_file_selector(
                label="Choose a TEI-File",
                key="tr_teifile",
                help="Choose a TEI file for testing the chosen TEI Reader Config",
            )
            if "tr_last_test_dict" not in st.session_state:
                st.session_state.tr_last_test_dict={}
            if st.button(
                "Test TEI Reader Config",
                key="tr_Button_Test",
                help="Test TEI Reader Config on the chosen Config and TEI-File.",
            ):
                if os.path.isfile(st.session_state.tr_teifile):
                    st.session_state.tr_last_test_dict = {
                        "teifile": st.session_state.tr_teifile,
                        "tr": config,
                    }
                else:
                    st.error(f"The chosen path {st.session_state.tr_teifile} is not a file!")
                    st.session_state.tr_last_test_dict = {}
            if (
                st.session_state.tr_last_test_dict
                and len(st.session_state.tr_last_test_dict.keys()) > 0
            ):
                tei = tp.TEIFile(
                    st.session_state.tr_last_test_dict["teifile"],
                    st.session_state.tr_last_test_dict["tr"],
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
        tr_show_configs = st.expander("Existing TEI Reader Configs", expanded=True)
        with tr_show_configs:
            st.markdown(self.build_config_tablestring())
            st.markdown(" ")  # only for layouting reasons (placeholder)

    def show(self):
        st.latex("\\text{\Huge{TEI Reader Config}}")
        col1, col2 = st.columns(2)
        with col1:
            self.show_configs()
        with col2:
            self.show_edit_environment()
        self.show_test_environment()
