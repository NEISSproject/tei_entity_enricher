import logging
import os
import shutil

import streamlit as st

import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_ner_gb as gb
from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.aip_interface.trainer_params import NERTrainerParams, get_params
from tei_entity_enricher.util.components import small_dir_selector
from tei_entity_enricher.util.helper import (
    module_path,
    state_ok,
    file_lists_entry_widget,
    numbers_lists_entry_widget,
    remember_cwd,
    menu_entity_definition,
    menu_groundtruth_builder,
    menu_NER_trainer,
)
from tei_entity_enricher.util.aip_interface.processmanger.train import get_train_process_manager

logger = logging.getLogger(__name__)


class NERTrainer(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd = os.getcwd()
        self.training_state = None
        self._data_config_check = []
        self.selected_train_list = None
        self.train_process_manager = None
        self.train_conf_options = {
            f"Groundtruth from {menu_groundtruth_builder}": self.data_conf_by_tei_gb,
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
    def _params(self) -> NERTrainerParams:
        return get_params()

    def show(self):
        st.latex("\\text{\Huge{" + menu_NER_trainer + "}}")
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
        self.train_process_manager.set_current_params(self._params)
        return_code = self.train_process_manager.st_manager()
        return return_code

    def data_configuration(self) -> int:
        self._data_config_check = []

        with remember_cwd():
            os.chdir(self._wd)
            with st.expander("Train configuration", expanded=True):

                if self._params.trainer_params_json is None:
                    # only new loading if necessary, otherwise everytime the old trainer_params_json is loaded
                    logger.info("load trainer params")
                    if self.load_trainer_params() != 0:
                        st.error("Failed to load trainer_params.json")
                        logger.error("Failed to load trainer_params.json")
                        return -1

                st.radio(
                    label="Train configuration options",
                    options=tuple(self.train_conf_options.keys()),
                    key="nt_train_option",
                    help="Choose an option to define a train configuration.",
                )

                self.train_conf_options[st.session_state.nt_train_option]()

                label = "pretrained model"
                if self._params.scan_models(target_dir=os.path.join(self._wd, "models_pretrained")) != 0:
                    self._params.possible_models = {f"no {label} found": None}
                    self._data_config_check.append(f"no {label} found")
                self._params.choose_model_widget(
                    label, init=self._params.trainer_params_json["scenario"]["model"]["pretrained_bert"]
                )
                if self._params.is_hf_model:
                    self._params.trainer_params_json["scenario"]["model"]["model"] = "NERwithHFBERT"
                    self._params.trainer_params_json["scenario"]["data"]["use_hf_model"] = True
                    self._params.trainer_params_json["scenario"]["data"]["pretrained_hf_model"] = self._params.model
                    self._params.trainer_params_json["gen"]["setup"]["train"]["batch_size"] = 8
                    self._params.trainer_params_json["gen"]["setup"]["val"]["batch_size"] = 8
                    self._params.trainer_params_json["samples_per_epoch"]=1250
                else:
                    self._params.trainer_params_json["scenario"]["model"]["model"] = "NERwithMiniBERT"
                    self._params.trainer_params_json["scenario"]["data"]["use_hf_model"] = False
                    self._params.trainer_params_json["scenario"]["model"]["pretrained_bert"] = self._params.model
                    self._params.trainer_params_json["gen"]["setup"]["train"]["batch_size"] = 16
                    self._params.trainer_params_json["gen"]["setup"]["val"]["batch_size"] = 16
                    self._params.trainer_params_json["samples_per_epoch"]=5000

                if self.set_output_directory() != 0:
                    self._data_config_check.append("Invalid output directory")

                self._params.trainer_params_json["epochs"] = st.number_input(
                    label="Epochs to train",
                    min_value=1,
                    value=self._params.trainer_params_json["epochs"],
                    step=1,
                    help="Insert the number of epochs your model should be trained for. I you have no idea we suggest 30 epochs for a training.",
                )

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
        st.selectbox(
            label=f"Choose an {menu_entity_definition}",
            options=tuple(self.ntd.defdict.keys()),
            key="nt_sel_ntd_name",
            help=f"To specify which NER task you want to train choose an {menu_entity_definition}.",
        )
        self._params.trainer_params_json["scenario"]["data"]["tags"] = self.ntd.get_tag_filepath_to_ntdname(
            st.session_state.nt_sel_ntd_name
        )

        st.radio(
            label="Input data Source",
            options=tuple(self.train_list_options.keys()),
            key="nt_train_list_option",
            help="Choose an option for define where your input data should come from.",
        )

        self.train_list_options[st.session_state.nt_train_list_option]()

    def set_output_directory(self):
        value = os.path.relpath(
            self._params.trainer_params_json["output_dir"], os.path.abspath(os.path.join(self._wd, "models_ner"))
        )
        st.text_input(label="output dir", key="nt.ti.output_dir", value=value)

        models_ner_dir = os.path.abspath(os.path.join(self._wd, "models_ner"))
        if os.path.isdir(os.path.join(models_ner_dir, st.session_state["nt.ti.output_dir"])):
            elements_to_delete = [
                os.path.join(models_ner_dir, st.session_state["nt.ti.output_dir"], element)
                for element in os.listdir(os.path.join(models_ner_dir, st.session_state["nt.ti.output_dir"]))
                if not element.endswith(".lst")
            ]
            if len(elements_to_delete) > 0:
                a, b = st.columns(2)
                a.warning(f"Output dir is not empty! Do you really want to empty it?")

                def delete_all_content(elements_to_delete):
                    for element in elements_to_delete:
                        if os.path.isfile(element):
                            os.remove(element)
                        else:
                            shutil.rmtree(element)

                b.button(
                    f'Delete all content of: {os.path.join(models_ner_dir, st.session_state["nt.ti.output_dir"])}',
                    on_click=delete_all_content,
                    args=(elements_to_delete,),
                )

                return -1
        else:
            a, b = st.columns(2)
            a.info(f"Output dir does not exist! Do you want to create it?")

            def create_output_dir():
                os.makedirs(os.path.join(models_ner_dir, st.session_state["nt.ti.output_dir"]))
                self._params.trainer_params_json["output_dir"] = os.path.join(
                    models_ner_dir, st.session_state["nt.ti.output_dir"]
                )

            b.button(
                f'Create: {os.path.join(models_ner_dir, st.session_state["nt.ti.output_dir"])}',
                on_click=create_output_dir,
            )
            return -1
        self._params.trainer_params_json["output_dir"] = os.path.join(
            models_ner_dir, st.session_state["nt.ti.output_dir"]
        )

        self._params.trainer_params_json["early_stopping"]["best_model_output_dir"] = os.path.join(
            models_ner_dir, st.session_state["nt.ti.output_dir"]
        )

        return 0

    def data_conf_by_tei_gb(self):
        st.selectbox(
            label="Choose a Groundtruth",
            options=tuple(self.tng.tngdict.keys()),
            key="nt_sel_tng_name",
            help="Choose a Groundtruth which you want to use for training.",
        )
        ntd_name = self.tng.tngdict[st.session_state.nt_sel_tng_name][self.tng.tng_attr_tnm]["ntd"][
            self.ntd.ntd_attr_name
        ]
        self._params.trainer_params_json["scenario"]["data"]["tags"] = self.ntd.get_tag_filepath_to_ntdname(ntd_name)
        trainlistfilepath, devlistfilepath, testlistfilepath = self.tng.get_filepath_to_gt_lists(
            st.session_state.nt_sel_tng_name
        )
        self._params.trainer_params_json["gen"]["train"]["lists"] = [trainlistfilepath]
        self._params.trainer_params_json["gen"]["val"]["lists"] = [devlistfilepath]

    def data_list_conf_from_folder(self):
        train_dir, train_dir_state = small_dir_selector(
            label="Folder with Train-JSON-Files",
            value=os.path.dirname(self._params.trainer_params_json["gen"]["train"]["lists"][0])
            if os.path.isfile(self._params.trainer_params_json["gen"]["train"]["lists"][0])
            else self._params.trainer_params_json["gen"]["train"]["lists"][0],
            key="nt_conf_train_dir",
            help="Choose a directory with json-Files which should be used for Training.",
            return_state=True,
        )
        if train_dir_state == state_ok and st.session_state.nt_conf_train_dir != self._params.nt_train_dir:
            self._params.nt_train_dir = st.session_state.nt_conf_train_dir
        elif train_dir_state != state_ok:
            self._data_config_check.append("Folder with Train-JSON-Files")

        val_dir, val_dir_state = small_dir_selector(
            label="Folder with Validation-JSON-Files",
            value=os.path.dirname(self._params.trainer_params_json["gen"]["val"]["lists"][0])
            if os.path.isfile(self._params.trainer_params_json["gen"]["val"]["lists"][0])
            else self._params.trainer_params_json["gen"]["val"]["lists"][0],
            key="nt_conf_val_dir",
            help="Choose a directory with json-Files which should be used for the evaluation in between the training.",
            return_state=True,
        )
        if val_dir_state == state_ok and st.session_state.nt_conf_val_dir != self._params.nt_val_dir:
            self._params.nt_val_dir = st.session_state.nt_conf_val_dir
        elif val_dir_state != state_ok:
            self._data_config_check.append("Folder with Validation-JSON-Files")

    def data_list_conf_from_lst(self):
        train_lists = file_lists_entry_widget(
            self._params.trainer_params_json["gen"]["train"]["lists"],
            name="train.lists",
            help=", separated file names",
        )
        if train_lists:
            self._params.trainer_params_json["gen"]["train"]["lists"] = train_lists

        if len(train_lists) > 1 or len(self._params.trainer_params_json["gen"]["train"]["list_ratios"]) > 1:
            train_lists_ratio = numbers_lists_entry_widget(
                self._params.trainer_params_json["gen"]["train"]["list_ratios"],
                name="train.list_ratios",
                expect_amount=len(train_lists),
                help="e.g. '1.0, 2.0' must be same amount as file names",
            )
            if train_lists_ratio:
                self._params.trainer_params_json["gen"]["train"]["list_ratios"] = train_lists_ratio
            else:
                self._data_config_check.append("train.list_ratios")
        val_lists = file_lists_entry_widget(
            self._params.trainer_params_json["gen"]["val"]["lists"],
            name="val.lists",
            help=", separated file names",
        )
        if val_lists:
            self._params.trainer_params_json["gen"]["val"]["lists"] = val_lists
            # self.save_train_params()
        else:
            self._data_config_check.append("val.lists")
        if len(val_lists) > 1 or len(self._params.trainer_params_json["gen"]["val"]["list_ratios"]) > 1:
            val_lists_ratio = numbers_lists_entry_widget(
                self._params.trainer_params_json["gen"]["val"]["list_ratios"],
                name="val.list_ratios",
                expect_amount=len(val_lists),
                help="e.g. '1.0, 2.0' must be same amount as file names",
            )
            if val_lists_ratio:
                self._params.trainer_params_json["gen"]["val"]["list_ratios"] = val_lists_ratio
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

    def load_trainer_params(self):
        with remember_cwd():
            os.chdir(self._wd)
            self._params.trainer_params_json = config_io.get_config("trainer_params.json")
        return 0

    def save_train_params(self):
        self.train_process_manager = get_train_process_manager(workdir=self._wd)
        self.train_process_manager.set_current_params(self._params)
        return self.train_process_manager.save_train_params()
