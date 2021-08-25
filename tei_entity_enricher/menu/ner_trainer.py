import glob
import logging
import os
import shutil

import streamlit as st

import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_ner_gb as gb
from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.components import small_dir_selector, selectbox_widget, radio_widget, text_input_widget
from tei_entity_enricher.util.helper import (
    module_path,
    state_ok,
    file_lists_entry_widget,
    numbers_lists_entry_widget,
    model_dir_entry_widget,
    remember_cwd,
)
from tei_entity_enricher.util.processmanger.train import get_train_process_manager
from dataclasses import dataclass, field
from typing import Dict

from dataclasses_json import dataclass_json

logger = logging.getLogger(__name__)


@dataclass
@dataclass_json
class NERTrainerParams:
    nt_trainer_params_json: Dict = None
    nt_train_option: str = None
    nt_sel_ntd_name: str = None
    nt_train_list_option: str = None
    nt_sel_tng_name: str = None
    nt_train_dir: str = None
    nt_val_dir: str = None
    # nt_pretrained_model: str = None # moved to nt_train_params_json
    nt_pretrained_models: Dict = None
    nt_output_dir: str = None


@st.cache(allow_output_mutation=True)
def get_params() -> NERTrainerParams:
    return NERTrainerParams()


class NERTrainer(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd = os.getcwd()
        self.training_state = None
        self._data_config_check = []
        self.selected_train_list = None
        self.train_process_manager = None
        self.train_conf_options = {
            "TEI NER Groundtruth": self.data_conf_by_tei_gb,
            "Self-Defined": self.data_conf_self_def,
        }
        self.train_list_options = {
            "From Folder": self.data_list_conf_from_folder,
            "From Lst-File": self.data_list_conf_from_lst,
        }
        if self.workdir() != 0:
            return
        if self.show_menu:
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.tng = gb.TEINERGroundtruthBuilder(show_menu=False)
            self.show()

    @property
    def ner_trainer_params(self) -> NERTrainerParams:
        return get_params()

    def show(self):
        if self.workdir() != 0:
            return -1

        if not get_train_process_manager(workdir=self._wd).has_process():
            if self.data_configuration() != 0:
                return -1

        if self._train_manager() != 0:
            return -1

        st.latex(state_ok)

    def check(self, verbose: str = "none", **kwargs) -> str:
        """verbose: 'none', 'console', 'streamlit'"""
        # TODO: make pre-training check
        return ""

    def _train_manager(self):
        self.train_process_manager = get_train_process_manager(workdir=self._wd)
        return_code = self.train_process_manager.st_manager()
        return return_code

    def data_configuration(self) -> int:
        self._data_config_check = []

        with remember_cwd():
            os.chdir(self._wd)
            with st.beta_expander("Train configuration", expanded=True):

                if self.ner_trainer_params.nt_trainer_params_json is None:
                    # only new loading if necessary, otherwise everytime the old trainer_params_json is loaded
                    logger.info("load trainer params")
                    if self.load_trainer_params() != 0:
                        st.error("Failed to load trainer_params.json")
                        logger.error("Failed to load trainer_params.json")
                        return -1

                self.ner_trainer_params.nt_train_option = radio_widget(
                    "Train configuration options",
                    tuple(self.train_conf_options.keys()),
                    tuple(self.train_conf_options.keys()).index(self.ner_trainer_params.nt_train_option)
                    if self.ner_trainer_params.nt_train_option
                    else 0,
                    key="nt_train_option",
                    help="Choose an option to define a train configuration.",
                )

                self.train_conf_options[self.ner_trainer_params.nt_train_option]()

                # pretrained_model = model_dir_entry_widget(
                #     self.ner_trainer_params.nt_trainer_params_json["scenario"]["model"]["pretrained_bert"],
                #     name="model.pretrained_bert",
                #     expect_saved_model=True,
                # )

                self.choose_pretained_model()

                # output_dir = text_entry_with_check(
                #    string=self.ner_trainer_params.nt_trainer_params_json["output_dir"],
                #    name="output_dir",
                #    check_fn=check_dir_ask_make,
                # )
                # if output_dir:
                #    self.ner_trainer_params.nt_trainer_params_json["output_dir"] = output_dir
                #    self.save_train_params()
                # else:
                #    self._data_config_check.append("output_dir")

                if self.set_output_directory() != 0:
                    self._data_config_check.append("Invalid output directory")

                if self._data_config_check:
                    st.error(f"Fix {self._data_config_check} to continue!")
                    logger.error(f"Fix {self._data_config_check} to continue!")
                    return -1
                else:
                    logger.info("data configuration successful")
                    if st.button(f'Save trainer_params to config: {os.path.join(self._wd, "trainer_params.json")}'):
                        if self.save_train_params() != 0:
                            st.error("Failed to save trainer_params.json")
                            logger.error("Failed to save trainer_params.json")
                        logger.info(f'trainer params saved to: {os.path.join(self._wd, "trainer_params.json")}')
                        st.experimental_rerun()
                    return 0

    def data_conf_self_def(self):
        self.ner_trainer_params.nt_sel_ntd_name = selectbox_widget(
            "Choose an NER Task",
            tuple(self.ntd.defdict.keys()),
            tuple(self.ntd.defdict.keys()).index(self.ner_trainer_params.nt_sel_ntd_name)
            if self.ner_trainer_params.nt_sel_ntd_name
            else 0,
            key="nt_sel_ntd",
            help="To specify which NER task you want to train choose an NER Task Entity Definition.",
        )
        self.ner_trainer_params.nt_trainer_params_json["scenario"]["data"][
            "tags"
        ] = self.ntd.get_tag_filepath_to_ntdname(self.ner_trainer_params.nt_sel_ntd_name)

        self.ner_trainer_params.nt_train_list_option = radio_widget(
            "Input data Source",
            tuple(self.train_list_options.keys()),
            tuple(self.train_list_options.keys()).index(self.ner_trainer_params.nt_train_list_option)
            if self.ner_trainer_params.nt_train_list_option
            else 0,
            key="nt_train_list_option",
            help="Choose an option for define where your input data should come from.",
        )

        self.train_list_options[self.ner_trainer_params.nt_train_list_option]()

    def scan_pretrained_models(self):
        possible_paths = []
        for root, subdirs, files in os.walk(os.path.join(self._wd, "models_pretrained")):
            # print(root, subdirs, files)
            if "encoder_only" in subdirs and os.path.isfile(os.path.join(root, "encoder_only", "saved_model.pb")):
                possible_paths.append(root)

        logger.debug(f"pretrained model possible_paths: {possible_paths}")
        self.ner_trainer_params.nt_pretrained_models = dict(
            (os.path.relpath(x, os.path.join(self._wd, "models_pretrained")), x) for x in possible_paths
        )
        logger.debug(f"pretrained model dict: {self.ner_trainer_params.nt_pretrained_models}")
        return 0 if possible_paths else -1

    def choose_pretained_model(self):
        if self.scan_pretrained_models() != 0:
            self._data_config_check.append("No pretrained model found!")
            self.ner_trainer_params.nt_pretrained_models = {"no model found": None}

        pretrained_model_key = selectbox_widget(
            "Choose a pretrained BERT model",
            tuple(self.ner_trainer_params.nt_pretrained_models.keys()),
            tuple(self.ner_trainer_params.nt_pretrained_models.keys()).index(
                self.ner_trainer_params.nt_trainer_params_json["scenario"]["model"]["pretrained_bert"]
            )
            if self.ner_trainer_params.nt_trainer_params_json["scenario"]["model"]["pretrained_bert"]
            in tuple(self.ner_trainer_params.nt_pretrained_models.keys())
            else 0,
            key="nt_select_pretrained_model",
            help="Choose a pretrained BERT model (encoder only), which you want to use for training.",
        )
        self.ner_trainer_params.nt_trainer_params_json["scenario"]["model"][
            "pretrained_bert"
        ] = self.ner_trainer_params.nt_pretrained_models[pretrained_model_key]

    def set_output_directory(self):
        self.ner_trainer_params.nt_output_dir = text_input_widget(
            "New NER Task Entity Definition Name:",
            os.path.relpath(
                self.ner_trainer_params.nt_trainer_params_json["output_dir"],
                os.path.abspath(os.path.join(self._wd, "models_ner")),
            ),
        )
        with remember_cwd():
            os.chdir(os.path.abspath(os.path.join(self._wd, "models_ner")))
            if os.path.isdir(self.ner_trainer_params.nt_output_dir):
                if len(os.listdir(self.ner_trainer_params.nt_output_dir)) > 0:
                    a, b = st.beta_columns(2)
                    a.warning(f"Output dir is not empty! Do you really want to empty it?")
                    if b.button(
                        f"Delete all content of: {os.path.join(os.getcwd(), self.ner_trainer_params.nt_output_dir)}"
                    ):
                        shutil.rmtree(os.path.join(os.getcwd(), self.ner_trainer_params.nt_output_dir))
                        os.makedirs(os.path.join(os.getcwd(), self.ner_trainer_params.nt_output_dir))
                        st.experimental_rerun()
                    return -1
            else:
                a, b = st.beta_columns(2)
                a.info(f"Output dir does not exist! Do you want to create it?")
                if b.button(f"Create: {os.path.join(os.getcwd(), self.ner_trainer_params.nt_output_dir)}"):
                    os.makedirs(os.path.join(os.getcwd(), self.ner_trainer_params.nt_output_dir))
                    self.ner_trainer_params.nt_trainer_params_json["output_dir"] = os.path.join(
                        os.getcwd(), self.ner_trainer_params.nt_output_dir
                    )
                    st.experimental_rerun()
                return -1
            self.ner_trainer_params.nt_trainer_params_json["output_dir"] = os.path.join(
                os.getcwd(), self.ner_trainer_params.nt_output_dir
            )
            self.ner_trainer_params.nt_trainer_params_json["early_stopping"]["best_model_output_dir"] = os.path.join(
                os.getcwd(), self.ner_trainer_params.nt_output_dir
            )

        return 0

    def data_conf_by_tei_gb(self):
        self.ner_trainer_params.nt_sel_tng_name = selectbox_widget(
            "Choose a Groundtruth",
            tuple(self.tng.tngdict.keys()),
            tuple(self.tng.tngdict.keys()).index(self.ner_trainer_params.nt_sel_tng_name)
            if self.ner_trainer_params.nt_sel_tng_name
            else 0,
            key="nt_sel_tng",
            help="Choose a TEI NER Groundtruth which you want to use for training.",
        )
        ntd_name = self.tng.tngdict[self.ner_trainer_params.nt_sel_tng_name][self.tng.tng_attr_tnm]["ntd"][
            self.ntd.ntd_attr_name
        ]
        self.ner_trainer_params.nt_trainer_params_json["scenario"]["data"][
            "tags"
        ] = self.ntd.get_tag_filepath_to_ntdname(ntd_name)
        trainlistfilepath, devlistfilepath, testlistfilepath = self.tng.get_filepath_to_gt_lists(
            self.ner_trainer_params.nt_sel_tng_name
        )
        self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"] = [trainlistfilepath]
        self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"] = [devlistfilepath]

    def data_list_conf_from_folder(self):
        train_dir, train_dir_state = small_dir_selector(
            "Folder with Train-JSON-Files",
            self.ner_trainer_params.nt_train_dir
            if self.ner_trainer_params.nt_train_dir
            else (
                os.path.dirname(self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"][0])
                if os.path.isfile(self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"][0])
                else self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"][0]
            ),
            key="nt_conf_train_dir",
            help="Choose a directory with json-Files which should be used for Training.",
            return_state=True,
        )
        if train_dir_state == state_ok and train_dir != self.ner_trainer_params.nt_train_dir:
            self.ner_trainer_params.nt_train_dir = train_dir
        elif train_dir_state != state_ok:
            self._data_config_check.append("Folder with Train-JSON-Files")

        val_dir, val_dir_state = small_dir_selector(
            "Folder with Validation-JSON-Files",
            self.ner_trainer_params.nt_val_dir
            if self.ner_trainer_params.nt_val_dir
            else (
                os.path.dirname(self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"][0])
                if os.path.isfile(self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"][0])
                else self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"][0]
            ),
            key="nt_conf_val_dir",
            help="Choose a directory with json-Files which should be used for the evaluation in between the training.",
            return_state=True,
        )
        if val_dir_state == state_ok and val_dir != self.ner_trainer_params.nt_val_dir:
            self.ner_trainer_params.nt_val_dir = val_dir
        elif val_dir_state != state_ok:
            self._data_config_check.append("Folder with Validation-JSON-Files")

    def data_list_conf_from_lst(self):
        train_lists = file_lists_entry_widget(
            self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"],
            name="train.lists",
            help=", separated file names",
        )
        if train_lists:
            self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"] = train_lists

        if (
            len(train_lists) > 1
            or len(self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["list_ratios"]) > 1
        ):
            train_lists_ratio = numbers_lists_entry_widget(
                self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["list_ratios"],
                name="train.list_ratios",
                expect_amount=len(train_lists),
                help="e.g. '1.0, 2.0' must be same amount as file names",
            )
            if train_lists_ratio:
                self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["list_ratios"] = train_lists_ratio
            else:
                self._data_config_check.append("train.list_ratios")
        val_lists = file_lists_entry_widget(
            self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"],
            name="val.lists",
            help=", separated file names",
        )
        if val_lists:
            self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"] = val_lists
            # self.save_train_params()
        else:
            self._data_config_check.append("val.lists")
        if len(val_lists) > 1 or len(self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["list_ratios"]) > 1:
            val_lists_ratio = numbers_lists_entry_widget(
                self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["list_ratios"],
                name="val.list_ratios",
                expect_amount=len(val_lists),
                help="e.g. '1.0, 2.0' must be same amount as file names",
            )
            if val_lists_ratio:
                self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["list_ratios"] = val_lists_ratio
                # self.save_train_params()
            else:
                self._data_config_check.append("val.list_ratios")

    def get_workdir(self):
        return self._wd

    def workdir(self):
        if module_path.lower() != os.path.join(os.getcwd(), "tei_entity_enricher", "tei_entity_enricher").lower():
            if self.show_menu:
                st.error("Please run ntee-start from the directory which contains the git repos 'tei_entity_enricher'.")
            else:
                logging.error(
                    "Please run ntee-start from the directory which contains the git repos 'tei_entity_enricher'."
                )
            return -1

        self._wd = os.path.join(os.getcwd(), "ner_trainer")
        if not os.path.isdir(self._wd):
            st.error(
                f"The working directory for ner_trainer does not exist yet. Do you want to create the directory: {self._wd}?"
            )
            if st.button(f"Create: {self._wd}"):
                if not os.path.isdir(self._wd):
                    os.makedirs(self._wd)
            return -1

        if not os.path.isfile(os.path.join(self._wd, "trainer_params.json")):
            shutil.copy(
                os.path.join(module_path, "templates", "trainer", "template_wd", "trainer_params.json"),
                self._wd,
            )
        if not os.path.isdir(os.path.join(self._wd, "templates")):
            shutil.copytree(
                os.path.join(module_path, "templates", "trainer", "template_wd", "templates"),
                os.path.join(self._wd, "templates"),
            )

        return 0

    def build_lst_files_if_necessary(self):
        if (
            self.ner_trainer_params.nt_train_option == "Self-Defined"
            and self.ner_trainer_params.nt_train_list_option == "From Folder"
        ):
            if os.path.isdir(self.ner_trainer_params.nt_train_dir):
                trainfilelist = [
                    os.path.join(self.ner_trainer_params.nt_train_dir, filepath + "\n")
                    for filepath in os.listdir(self.ner_trainer_params.nt_train_dir)
                    if filepath.endswith(".json")
                ]
                with open(
                    os.path.join(
                        self.ner_trainer_params.nt_trainer_params_json["output_dir"],
                        "train.lst",
                    ),
                    "w+",
                ) as htrain:
                    htrain.writelines(trainfilelist)
                self.ner_trainer_params.nt_trainer_params_json["gen"]["train"]["lists"] = [
                    os.path.join(
                        self.ner_trainer_params.nt_trainer_params_json["output_dir"],
                        "train.lst",
                    )
                ]
            if os.path.isdir(self.ner_trainer_params.nt_val_dir):
                valfilelist = [
                    os.path.join(self.ner_trainer_params.nt_val_dir, filepath + "\n")
                    for filepath in os.listdir(self.ner_trainer_params.nt_val_dir)
                    if filepath.endswith(".json")
                ]
                with open(
                    os.path.join(
                        self.ner_trainer_params.nt_trainer_params_json["output_dir"],
                        "val.lst",
                    ),
                    "w+",
                ) as hval:
                    hval.writelines(valfilelist)
                self.ner_trainer_params.nt_trainer_params_json["gen"]["val"]["lists"] = [
                    os.path.join(
                        self.ner_trainer_params.nt_trainer_params_json["output_dir"],
                        "val.lst",
                    )
                ]

    def load_trainer_params(self):
        with remember_cwd():
            os.chdir(self._wd)
            self.ner_trainer_params.nt_trainer_params_json = config_io.get_config("trainer_params.json")
        return 0

    def save_train_params(self):
        self.build_lst_files_if_necessary()
        with remember_cwd():
            os.chdir(self._wd)
            config_io.set_config(self.ner_trainer_params.nt_trainer_params_json)
        return 0
