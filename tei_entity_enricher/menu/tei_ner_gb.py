import streamlit as st
import json
import os
import random
import math
import shutil
import traceback

from tei_entity_enricher.util.helper import (
    module_path,
    local_save_path,
    makedir_if_necessary,
    menu_TEI_reader_config,
    menu_TEI_read_mapping,
    menu_groundtruth_builder,
    print_st_message,
    is_accepted_TEI_filename,
    check_folder_for_TEI_Files,
    MessageType,
)
import tei_entity_enricher.menu.tei_ner_map as tei_map
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.util.tei_parser as tp
from tei_entity_enricher.util.spacy_lm import lang_dict, get_spacy_lm
from tei_entity_enricher.util.components import small_dir_selector


class TEINERGroundtruthBuilder:
    def __init__(self, show_menu=True):
        self.tng_Folder = "TNG"
        self.template_tng_Folder = os.path.join(module_path, "templates", self.tng_Folder)
        self.tng_Folder = os.path.join(local_save_path, self.tng_Folder)
        self.tng_attr_name = "name"
        self.tng_attr_tr = "tr"
        self.tng_attr_tnm = "tnm"
        self.tng_attr_lang = "lang"
        self.tng_attr_ratio = "ratio"
        self.tng_attr_shuffle_type = "shuffle_type"
        self.tng_attr_template = "template"
        self.tng_gt_type_train = "train"
        self.tng_gt_type_dev = "dev"
        self.tng_gt_type_test = "test"
        self.check_one_time_attributes()

        self.shuffle_options_dict = {
            "Shuffle by TEI File": True,
            "Shuffle by Sentences": False,
        }

        makedir_if_necessary(self.tng_Folder)
        makedir_if_necessary(self.template_tng_Folder)

        self.refresh_tng_list()

        if show_menu:
            self.tnm = tei_map.TEINERMap(show_menu=False)
            self.tr = tei_reader.TEIReader(show_menu=False)
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.show()
            self.check_rerun_messages()

    def check_rerun_messages(self):
        if "tng_rerun_save_message" in st.session_state and st.session_state.tng_rerun_save_message is not None:
            st.session_state.tng_save_message = st.session_state.tng_rerun_save_message
            st.session_state.tng_rerun_save_message = None
            st.experimental_rerun()

    def check_one_time_attributes(self):
        if "tng_save_message" in st.session_state and st.session_state.tng_save_message is not None:
            self.tng_save_message = st.session_state.tng_save_message
            st.session_state.tng_save_message = None
        else:
            self.tng_save_message = None

    def refresh_tng_list(self):
        self.tnglist = []
        for gt_folder in sorted(os.listdir(self.template_tng_Folder)):
            if os.path.isdir(os.path.join(self.template_tng_Folder, gt_folder)) and os.path.isfile(
                os.path.join(self.template_tng_Folder, gt_folder, os.path.basename(gt_folder) + ".json")
            ):
                with open(
                    os.path.join(
                        self.template_tng_Folder,
                        gt_folder,
                        os.path.basename(gt_folder) + ".json",
                    )
                ) as f:
                    self.tnglist.append(json.load(f))
        for gt_folder in sorted(os.listdir(self.tng_Folder)):
            if os.path.isdir(os.path.join(self.tng_Folder, gt_folder)) and os.path.isfile(
                os.path.join(self.tng_Folder, gt_folder, os.path.basename(gt_folder) + ".json")
            ):
                with open(
                    os.path.join(
                        self.tng_Folder,
                        gt_folder,
                        os.path.basename(gt_folder) + ".json",
                    )
                ) as f:
                    self.tnglist.append(json.load(f))

        self.tngdict = {}
        self.editable_tng_names = []
        for tng in self.tnglist:
            self.tngdict[tng[self.tng_attr_name]] = tng
            if not tng[self.tng_attr_template]:
                self.editable_tng_names.append(tng[self.tng_attr_name])

    def validate_build_configuration(self, build_config, folder_path):
        val = True
        if (
            self.tng_attr_name not in build_config.keys()
            or build_config[self.tng_attr_name] is None
            or build_config[self.tng_attr_name] == ""
        ):
            val = False
            if self.tng_save_message is None:
                st.error("Please define a name for the Groundtruth before building it!")
        elif os.path.isdir(
            os.path.join(self.tng_Folder, build_config[self.tng_attr_name].replace(" ", "_"))
        ) and os.path.isfile(
            os.path.join(
                self.tng_Folder,
                build_config[self.tng_attr_name].replace(" ", "_"),
                build_config[self.tng_attr_name].replace(" ", "_") + ".json",
            )
        ):
            val = False
            if self.tng_save_message is None:
                st.error(
                    f"Choose another name. There is already a Groundtruth with name {build_config[self.tng_attr_name]}!"
                )
        if folder_path is None or folder_path == "":
            val = False
            if self.tng_save_message is None:
                st.error(
                    f"Please choose a folder containing the TEI-Files you want to use to build the groundtruth from!"
                )
        elif not os.path.isdir(folder_path):
            val = False
            if self.tng_save_message is None:
                st.error(f"The directory {folder_path} doesn't exist. Please choose valid directory!")
        if val:
            messageType, message = check_folder_for_TEI_Files(folder_path)
            if messageType != MessageType.success:
                print_st_message(messageType, message)
                if messageType == MessageType.error:
                    val = False
        return val

    def build_groundtruth(self, build_config, folder_path):
        build_config[self.tng_attr_template] = False
        progressoutput = st.success("Prepare Groundtruth building...")
        save_folder = os.path.join(self.tng_Folder, build_config[self.tng_attr_name].replace(" ", "_"))
        makedir_if_necessary(save_folder)
        save_test_folder = os.path.join(save_folder, self.tng_gt_type_test)
        makedir_if_necessary(save_test_folder)
        save_dev_folder = os.path.join(save_folder, self.tng_gt_type_dev)
        makedir_if_necessary(save_dev_folder)
        save_train_folder = os.path.join(save_folder, self.tng_gt_type_train)
        makedir_if_necessary(save_train_folder)

        nlp = get_spacy_lm(build_config[self.tng_attr_lang])
        by_file = self.shuffle_options_dict[build_config[self.tng_attr_shuffle_type]]
        filelist = os.listdir(folder_path)
        if not by_file:
            all_data = []
        else:
            random.shuffle(filelist)

        build_gb_progress_bar = st.progress(0)
        trainfilelist = []
        devfilelist = []
        testfilelist = []
        for fileindex in range(len(filelist)):
            if is_accepted_TEI_filename(filelist[fileindex]):
                progressoutput.success(f"Process file {filelist[fileindex]}...")
                try:
                    brief = tp.TEIFile(
                        os.path.join(folder_path, filelist[fileindex]),
                        build_config[self.tng_attr_tr],
                        entity_dict=build_config[self.tng_attr_tnm][self.tnm.tnm_attr_entity_dict],
                        nlp=nlp,
                        with_position_tags=True,
                    )
                except Exception as ex:
                    error_stack=' \n \n' + f'{repr(ex)}' + '\n \n' + "\n".join(traceback.TracebackException.from_exception(ex).format())
                    st.error(f'Groundtruth Building stopped: The Following error occurs, when trying to process TEI-File {filelist[fileindex]} : {error_stack}');
                    return

                raw_ner_data = tp.split_into_sentences(brief.build_tagged_text_line_list())
                if not by_file:
                    all_data.extend(raw_ner_data)
                else:
                    if fileindex <= (build_config[self.tng_attr_ratio][self.tng_gt_type_test] / 100.0) * len(filelist):
                        testfilepath = os.path.join(save_test_folder, filelist[fileindex] + ".json")
                        testfilelist.append(testfilepath + "\n")
                        with open(
                            testfilepath,
                            "w+",
                        ) as g:
                            json.dump(raw_ner_data, g)
                    elif fileindex <= (
                        (
                            build_config[self.tng_attr_ratio][self.tng_gt_type_test]
                            + build_config[self.tng_attr_ratio][self.tng_gt_type_dev]
                        )
                        / 100.0
                    ) * len(filelist):
                        devfilepath = os.path.join(save_dev_folder, filelist[fileindex] + ".json")
                        devfilelist.append(devfilepath + "\n")
                        with open(
                            devfilepath,
                            "w+",
                        ) as g:
                            json.dump(raw_ner_data, g)
                    else:
                        trainfilepath = os.path.join(save_train_folder, filelist[fileindex] + ".json")
                        trainfilelist.append(trainfilepath + "\n")
                        with open(
                            trainfilepath,
                            "w+",
                        ) as g:
                            json.dump(raw_ner_data, g)
            build_gb_progress_bar.progress(math.floor((fileindex + 1) / len(filelist) * 100))
        if not by_file:
            progressoutput.success("Shuffle and save the data...")
            random.shuffle(all_data)
            test_list = []
            dev_list = []
            train_list = []
            for data_index in range(len(all_data)):
                if data_index <= (build_config[self.tng_attr_ratio][self.tng_gt_type_test] / 100.0) * len(all_data):
                    test_list.append(all_data[data_index])
                elif data_index <= (
                    (
                        build_config[self.tng_attr_ratio][self.tng_gt_type_test]
                        + build_config[self.tng_attr_ratio][self.tng_gt_type_dev]
                    )
                    / 100.0
                ) * len(all_data):
                    dev_list.append(all_data[data_index])
                else:
                    train_list.append(all_data[data_index])
            testfilepath = os.path.join(
                save_test_folder,
                self.tng_gt_type_test + "_" + build_config[self.tng_attr_name].replace(" ", "_") + ".json",
            )
            testfilelist.append(testfilepath + "\n")
            with open(
                testfilepath,
                "w+",
            ) as g:
                json.dump(test_list, g)
            devfilepath = os.path.join(
                save_dev_folder,
                self.tng_gt_type_dev + "_" + build_config[self.tng_attr_name].replace(" ", "_") + ".json",
            )
            devfilelist.append(devfilepath + "\n")
            with open(
                devfilepath,
                "w+",
            ) as g2:
                json.dump(dev_list, g2)
            trainfilepath = os.path.join(
                save_train_folder,
                self.tng_gt_type_train + "_" + build_config[self.tng_attr_name].replace(" ", "_") + ".json",
            )
            trainfilelist.append(trainfilepath + "\n")
            with open(
                trainfilepath,
                "w+",
            ) as h:
                json.dump(train_list, h)
        with open(
            os.path.join(
                save_folder,
                build_config[self.tng_attr_name].replace(" ", "_") + ".json",
            ),
            "w+",
        ) as h2:
            json.dump(build_config, h2)
        with open(
            os.path.join(
                save_folder,
                self.tng_gt_type_test + "_" + build_config[self.tng_attr_name].replace(" ", "_") + ".lst",
            ),
            "w+",
        ) as htest:
            htest.writelines(testfilelist)
        with open(
            os.path.join(
                save_folder,
                self.tng_gt_type_dev + "_" + build_config[self.tng_attr_name].replace(" ", "_") + ".lst",
            ),
            "w+",
        ) as hdev:
            hdev.writelines(devfilelist)
        with open(
            os.path.join(
                save_folder,
                self.tng_gt_type_train + "_" + build_config[self.tng_attr_name].replace(" ", "_") + ".lst",
            ),
            "w+",
        ) as htrain:
            htrain.writelines(trainfilelist)
        progressoutput.success(f"Groundtruth {build_config[self.tng_attr_name]} succesfully builded.")
        st.write(f"Statistics for {build_config[self.tng_attr_name]}")
        self.show_statistics_to_saved_groundtruth(
            save_folder,
            build_config[self.tng_attr_tnm][self.tnm.tnm_attr_ntd][self.ntd.ntd_attr_entitylist],
        )
        self.refresh_tng_list()

    def build_tng_stats_tablestring(self, entity_list, train_stats, dev_stats, test_stats):
        tablestring = "Entity | \# All | \# Train | \# Test | \# Devel \n -----|-------|-------|-------|-------"
        for entity in entity_list:
            train_num = train_stats["B-" + entity] if "B-" + entity in train_stats.keys() else 0
            test_num = test_stats["B-" + entity] if "B-" + entity in test_stats.keys() else 0
            dev_num = dev_stats["B-" + entity] if "B-" + entity in dev_stats.keys() else 0
            tablestring += (
                "\n "
                + entity
                + " | "
                + str(train_num + test_num + dev_num)
                + " | "
                + str(train_num)
                + " | "
                + str(test_num)
                + " | "
                + str(dev_num)
            )
        train_num = train_stats["O"] if "O" in train_stats.keys() else 0
        test_num = test_stats["O"] if "O" in test_stats.keys() else 0
        dev_num = dev_stats["O"] if "O" in dev_stats.keys() else 0
        tablestring += (
            "\n "
            + "unlabeled words"
            + " | "
            + str(train_num + test_num + dev_num)
            + " | "
            + str(train_num)
            + " | "
            + str(test_num)
            + " | "
            + str(dev_num)
        )
        return tablestring

    def build_ner_statistics(self, directory):
        tag_collect = {}
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                with open(os.path.join(directory, filename)) as f:
                    training_data = json.load(f)
                for i in range(len(training_data)):
                    for j in range(len(training_data[i])):
                        if training_data[i][j][1] in tag_collect.keys():
                            tag_collect[training_data[i][j][1]] += 1
                        else:
                            tag_collect[training_data[i][j][1]] = 1
        return {k: v for k, v in sorted(tag_collect.items(), key=lambda item: item[1])}

    def show_statistics_to_saved_groundtruth(self, directory, entity_list):
        test_folder = os.path.join(directory, self.tng_gt_type_test)
        dev_folder = os.path.join(directory, self.tng_gt_type_dev)
        train_folder = os.path.join(directory, self.tng_gt_type_train)
        st.markdown(
            self.build_tng_stats_tablestring(
                entity_list,
                self.build_ner_statistics(train_folder),
                self.build_ner_statistics(dev_folder),
                self.build_ner_statistics(test_folder),
            ),
            unsafe_allow_html=True,
        )
        st.markdown(" ")  # only for layouting reasons (placeholder)

    def show_build_gt_environment(self):
        tng_dict = {}
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Define a name for the groundtruth:", key="tng_name")
            if "tng_name" in st.session_state:
                tng_dict[self.tng_attr_name] = st.session_state.tng_name
            st.selectbox(
                label="Select a language for the groundtruth (relevant for the split into sentences):",
                options=list(lang_dict.keys()),
                key="tng_lang",
            )
            if "tng_lang" in st.session_state:
                tng_dict[self.tng_attr_lang] = st.session_state.tng_lang
        with col2:
            st.selectbox(
                label=f"Select a {menu_TEI_reader_config} for Building the groundtruth:",
                options=list(self.tr.configdict.keys()),
                key="tng_tr_name",
            )
            if "tng_tr_name" in st.session_state:
                tng_dict[self.tng_attr_tr] = self.tr.configdict[st.session_state.tng_tr_name]
            # self.tei_ner_gb_params.tng_tnm_name =
            st.selectbox(
                label=f"Select a {menu_TEI_read_mapping} for Building the groundtruth:",
                options=list(self.tnm.mappingdict.keys()),
                key="tng_tnm_name",
            )
            if "tng_tnm_name" in st.session_state:
                tng_dict[self.tng_attr_tnm] = self.tnm.mappingdict[st.session_state.tng_tnm_name]

        col3, col4 = st.columns(2)
        col5, col6, col7 = st.columns([0.25, 0.25, 0.5])
        with col3:
            st.markdown("Define a ratio for the partition into train- development- and testset.")
        with col5:
            st.number_input(
                "Percentage for the test set",
                min_value=0,
                max_value=int(
                    100 - (st.session_state.tng_dev_percentage if "tng_dev_percentage" in st.session_state else 10)
                ),
                value=int(
                    10 if "tng_test_percentage" not in st.session_state else st.session_state.tng_test_percentage
                ),
                key="tng_test_percentage",
            )
        with col6:
            st.number_input(
                "Percentage for the validation set",
                min_value=0,
                max_value=int(100 - st.session_state.tng_test_percentage),
                value=int(10 if "tng_dev_percentage" not in st.session_state else st.session_state.tng_dev_percentage),
                key="tng_dev_percentage",
            )
        with col7:
            st.radio(
                label="Shuffle Options", options=tuple(self.shuffle_options_dict.keys()), key="tng_shuffle_options"
            )
            tng_dict[self.tng_attr_shuffle_type] = st.session_state.tng_shuffle_options
        col8, col9 = st.columns(2)
        with col8:
            st.write(
                "With this configuration you have ",
                100 - st.session_state.tng_dev_percentage - st.session_state.tng_test_percentage,
                "% of the data for the train set, ",
                st.session_state.tng_dev_percentage,
                "% for the development set and",
                st.session_state.tng_test_percentage,
                "% for the test set.",
            )
        small_dir_selector(
            label="Choose a Folder containing only TEI Files to build the groundtruth from:",
            key="tng_teifile_folder",
        )
        tng_dict[self.tng_attr_ratio] = {
            self.tng_gt_type_train: 100 - st.session_state.tng_dev_percentage - st.session_state.tng_test_percentage,
            self.tng_gt_type_dev: st.session_state.tng_dev_percentage,
            self.tng_gt_type_test: st.session_state.tng_test_percentage,
        }
        if st.button("Build Groundtruth"):
            if self.validate_build_configuration(tng_dict, st.session_state.tng_teifile_folder):
                self.build_groundtruth(tng_dict, st.session_state.tng_teifile_folder)

    def validate_gt_for_delete(self, groundtruth):
        val = True
        return val

    def show_del_environment(self):
        if len(self.editable_tng_names) > 0:
            # self.tei_ner_gb_params.tng_del_gt_name =
            st.selectbox(
                label="Select a groundtruth to delete!", options=self.editable_tng_names, key="tng_del_gt_name"
            )

            def delete_gt(groundtruth):
                shutil.rmtree(os.path.join(self.tng_Folder, groundtruth[self.tng_attr_name].replace(" ", "_")))
                if "tng_sel_display_name" in st.session_state:
                    del st.session_state["tng_sel_display_name"]
                del st.session_state["tng_del_gt_name"]
                st.session_state.tng_rerun_save_message = (
                    f"Groundtruth {groundtruth[self.tng_attr_name]} was succesfully deleted!"
                )

            if self.tng_save_message is not None:
                st.success(self.tng_save_message)
            if self.validate_gt_for_delete(self.tngdict[st.session_state["tng_del_gt_name"]]):
                st.button(
                    "Delete Selected Groundtruth",
                    on_click=delete_gt,
                    args=(self.tngdict[st.session_state["tng_del_gt_name"]],),
                )
        else:
            st.info("There is no self-defined Groundtruth to delete!")

    def build_tng_tablestring(self):
        tablestring = f"Name | {menu_TEI_reader_config} | {menu_TEI_read_mapping} | Language | Shuffle Type | Partition Ratio | Template \n -----|-------|-------|-------|-------|-------|-------"
        for tng in self.tnglist:
            if tng[self.tng_attr_template]:
                template = "yes"
            else:
                template = "no"
            if self.shuffle_options_dict[tng[self.tng_attr_shuffle_type]]:
                shuffle_type = "by file"
            else:
                shuffle_type = "by sentences"
            partition_ratio = f"Train: {tng[self.tng_attr_ratio][self.tng_gt_type_train]}%, Test: {tng[self.tng_attr_ratio][self.tng_gt_type_test]}%, Devel: {tng[self.tng_attr_ratio][self.tng_gt_type_dev]}%"
            tablestring += (
                "\n "
                + tng[self.tng_attr_name]
                + " | "
                + tng[self.tng_attr_tr][self.tr.tr_config_attr_name]
                + " | "
                + tng[self.tng_attr_tnm][self.tnm.tnm_attr_name]
                + " | "
                + tng[self.tng_attr_lang]
                + " | "
                + shuffle_type
                + " | "
                + partition_ratio
                + " | "
                + template
            )
        return tablestring

    def show_existing_tng(self):
        st.markdown(self.build_tng_tablestring())
        st.markdown(" ")  # only for layouting reasons (placeholder)
        # self.tei_ner_gb_params.tng_selected_display_tng_name = \
        st.selectbox(
            label=f"Choose a groundtruth for displaying its statistics:",
            options=list(self.tngdict.keys()),
            key="tng_sel_display_name",
        )
        if "tng_sel_display_name" in st.session_state:
            cur_sel_tng = self.tngdict[st.session_state.tng_sel_display_name]
            if cur_sel_tng[self.tng_attr_template]:
                cur_folder = self.template_tng_Folder
            else:
                cur_folder = self.tng_Folder
            self.show_statistics_to_saved_groundtruth(
                os.path.join(cur_folder, cur_sel_tng[self.tng_attr_name].replace(" ", "_")),
                cur_sel_tng[self.tng_attr_tnm][self.tnm.tnm_attr_ntd][self.ntd.ntd_attr_entitylist],
            )

    def show(self):
        st.latex("\\text{\Huge{" + menu_groundtruth_builder + "}}")
        tng_build_new = st.expander("Build new Groundtruth", expanded=False)
        with tng_build_new:
            self.show_build_gt_environment()
        tng_delete = st.expander("Delete existing Groundtruth", expanded=False)
        with tng_delete:
            self.show_del_environment()
        tng_show = st.expander("Show existing Groundtruth", expanded=True)
        with tng_show:
            self.show_existing_tng()

    def get_filepath_to_gt_lists(self, name):
        save_folder = os.path.join(self.tng_Folder, name.replace(" ", "_"))
        makedir_if_necessary(save_folder)
        testlistfilepath = os.path.join(
            save_folder,
            self.tng_gt_type_test + "_" + name.replace(" ", "_") + ".lst",
        )
        devlistfilepath = os.path.join(
            save_folder,
            self.tng_gt_type_dev + "_" + name.replace(" ", "_") + ".lst",
        )
        trainlistfilepath = os.path.join(
            save_folder,
            self.tng_gt_type_train + "_" + name.replace(" ", "_") + ".lst",
        )
        if self.tngdict[name][self.tng_attr_template]:
            if not (
                os.path.isfile(trainlistfilepath)
                and os.path.isfile(devlistfilepath)
                and os.path.isfile(testlistfilepath)
            ):
                templ_folder = os.path.join(self.template_tng_Folder, name.replace(" ", "_"))
                save_test_folder = os.path.join(templ_folder, self.tng_gt_type_test)
                save_dev_folder = os.path.join(templ_folder, self.tng_gt_type_dev)
                save_train_folder = os.path.join(templ_folder, self.tng_gt_type_train)
                testfilelist = [
                    os.path.join(save_test_folder, filepath + "\n")
                    for filepath in os.listdir(save_test_folder)
                    if filepath.endswith(".json")
                ]
                devfilelist = [
                    os.path.join(save_dev_folder, filepath + "\n")
                    for filepath in os.listdir(save_dev_folder)
                    if filepath.endswith(".json")
                ]
                trainfilelist = [
                    os.path.join(save_train_folder, filepath + "\n")
                    for filepath in os.listdir(save_train_folder)
                    if filepath.endswith(".json")
                ]
                with open(
                    os.path.join(
                        save_folder,
                        testlistfilepath,
                    ),
                    "w+",
                ) as htest:
                    htest.writelines(testfilelist)
                with open(
                    os.path.join(
                        save_folder,
                        devlistfilepath,
                    ),
                    "w+",
                ) as hdev:
                    hdev.writelines(devfilelist)
                with open(
                    os.path.join(
                        save_folder,
                        trainlistfilepath,
                    ),
                    "w+",
                ) as htrain:
                    htrain.writelines(trainfilelist)
        return trainlistfilepath, devlistfilepath, testlistfilepath
