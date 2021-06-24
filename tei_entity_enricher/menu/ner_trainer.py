import logging
import os
import shutil

import streamlit as st
import tei_entity_enricher.menu.ner_task_def as ner_task
import tei_entity_enricher.menu.tei_ner_gb as gb
from streamlit_ace import st_ace
from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.components import small_dir_selector
from tei_entity_enricher.util.helper import (
    module_path,
    state_ok,
    file_lists_entry_widget,
    numbers_lists_entry_widget,
    model_dir_entry_widget,
    text_entry_with_check,
    check_dir_ask_make,
    remember_cwd,
)
from tei_entity_enricher.util.train_manager import get_manager

logger = logging.getLogger(__name__)


class NERTrainer(MenuBase):
    def __init__(self, state, show_menu=True, **kwargs):
        super().__init__(state, show_menu)
        self._wd = os.getcwd()
        self.state = state
        self.training_state = None
        # self.trainer_params_json = None
        self.selected_train_list = None
        self.train_conf_options = {
            "TEI NER Groundtruth": self.data_conf_by_tei_gb,
            "Self-Defined": self.data_conf_self_def,
        }
        if self.workdir() != 0:
            return
        if self.show_menu:
            self.ntd = ner_task.NERTaskDef(state, show_menu=False)
            self.tng = gb.TEINERGroundtruthBuilder(state, show_menu=False)
            self.show()

    def show(self):
        if self.workdir() != 0:
            return

        if self.data_configuration() != 0:
            return

        if self._train_manager() != 0:
            return

        st.latex(state_ok)

    def check(self, verbose: str = "none", **kwargs) -> str:
        """verbose: 'none', 'console', 'streamlit'"""
        # TODO: make pre-training check
        return ""

    def _train_manager(self):
        train_manager = get_manager(workdir=self._wd)
        with st.beta_container():
            st.text("Train Manager")
            if st.button("Set trainer params"):
                train_manager.set_params(self.state.tng_trainer_params_json)
                logger.info("trainer params set!")
            b1, b2, b3, b4, process_status = st.beta_columns([2, 2, 2, 2, 6])
            if b1.button("Start"):
                train_manager.start()
            if b2.button("Stop"):
                train_manager.stop()
            if b3.button("Clear"):
                train_manager.clear_process()
            if b4.button("refresh"):
                logger.info("refresh streamlit")
            train_manager.process_state(st_element=process_status)

            if train_manager.has_process():
                with st.beta_expander("Epoch progress", expanded=True):
                    progress_str = train_manager.read_progress()
                    logger.info(progress_str)
                    st.text(progress_str)
            if train_manager.has_process():
                with st.beta_expander("Train log", expanded=True):
                    log_str = train_manager.log_content()
                    st_ace(
                        log_str,
                        language="powershell",
                        auto_update=True,
                        readonly=True,
                        height=300,
                        wrap=True,
                        font_size=12,
                    )
        return 0

    def data_configuration(self) -> int:
        data_config_check = []

        with remember_cwd():
            os.chdir(self._wd)
            with st.beta_expander("Train configuration", expanded=True):

                if self.state.tng_trainer_params_json is None:
                    # only new loading if necessary, otherwise everytime the old trainer_params_json is loaded
                    logger.info("load trainer params")
                    if self.load_trainer_params() != 0:
                        st.error("Failed to load trainer_params.json")
                        logger.error("Failed to load trainer_params.json")
                        return

                self.state.nt_train_option = st.radio(
                    "Train configuration options",
                    tuple(self.train_conf_options.keys()),
                    tuple(self.train_conf_options.keys()).index(self.state.nt_train_option)
                    if self.state.nt_train_option
                    else 0,
                    key="nt_train_option",
                    help="Choose an option to define a train configuration.",
                )

                self.train_conf_options[self.state.nt_train_option](data_config_check)

                pretrained_model = model_dir_entry_widget(
                    self.state.tng_trainer_params_json["scenario"]["model"]["pretrained_bert"],
                    name="model.pretrained_bert",
                    expect_saved_model=True,
                )
                if pretrained_model:
                    self.state.tng_trainer_params_json["scenario"]["model"]["pretrained_bert"] = pretrained_model
                else:
                    data_config_check.append("model.pretrained_bert")

                # output_dir = text_entry_with_check(
                #    string=self.state.tng_trainer_params_json["output_dir"],
                #    name="output_dir",
                #    check_fn=check_dir_ask_make,
                # )
                # if output_dir:
                #    self.state.tng_trainer_params_json["output_dir"] = output_dir
                #    self.save_train_params()
                # else:
                #    data_config_check.append("output_dir")

                output_dir, output_dir_state = small_dir_selector(
                    self.state,
                    "Output Directory",
                    self.state.tng_trainer_params_json["output_dir"],
                    key="nt_conf_output_dir",
                    help="Choose a directory where the training should be saved in.",
                    return_state=True,
                    ask_make=True,
                )
                if output_dir_state == state_ok and output_dir != self.state.tng_trainer_params_json["output_dir"]:
                    self.state.tng_trainer_params_json["output_dir"] = output_dir
                    # st.experimental_rerun()
                elif output_dir_state != state_ok:
                    data_config_check.append("Output Directory")

                if data_config_check:
                    st.error(f"Fix {data_config_check} to continue!")
                    logger.error(f"Fix {data_config_check} to continue!")
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

    def data_conf_self_def(self, data_config_check):
        self.state.nt_sel_ntd_name = st.selectbox(
            "Choose an NER Task",
            tuple(self.ntd.defdict.keys()),
            tuple(self.ntd.defdict.keys()).index(self.state.nt_sel_ntd_name) if self.state.nt_sel_ntd_name else 0,
            key="nt_sel_ntd",
            help="To specify which NER task you want to train choose an NER Task Entity Definition.",
        )
        self.state.tng_trainer_params_json["scenario"]["data"]["tags"] = self.ntd.get_tag_filepath_to_ntdname(
            self.state.nt_sel_ntd_name
        )

        train_lists = file_lists_entry_widget(
            self.state.tng_trainer_params_json["gen"]["train"]["lists"],
            name="train.lists",
            help=", separated file names",
        )
        if train_lists:
            self.state.tng_trainer_params_json["gen"]["train"]["lists"] = train_lists

        if len(train_lists) > 1 or len(self.state.tng_trainer_params_json["gen"]["train"]["list_ratios"]) > 1:
            train_lists_ratio = numbers_lists_entry_widget(
                self.state.tng_trainer_params_json["gen"]["train"]["list_ratios"],
                name="train.list_ratios",
                expect_amount=len(train_lists),
                help="e.g. '1.0, 2.0' must be same amount as file names",
            )
            if train_lists_ratio:
                self.state.tng_trainer_params_json["gen"]["train"]["list_ratios"] = train_lists_ratio
            else:
                data_config_check.append("train.list_ratios")
        val_lists = file_lists_entry_widget(
            self.state.tng_trainer_params_json["gen"]["val"]["lists"],
            name="val.lists",
            help=", separated file names",
        )
        if val_lists:
            self.state.tng_trainer_params_json["gen"]["val"]["lists"] = val_lists
            # self.save_train_params()
        else:
            data_config_check.append("val.lists")
        if len(val_lists) > 1 or len(self.state.tng_trainer_params_json["gen"]["val"]["list_ratios"]) > 1:
            val_lists_ratio = numbers_lists_entry_widget(
                self.state.tng_trainer_params_json["gen"]["val"]["list_ratios"],
                name="val.list_ratios",
                expect_amount=len(val_lists),
                help="e.g. '1.0, 2.0' must be same amount as file names",
            )
            if val_lists_ratio:
                self.state.tng_trainer_params_json["gen"]["val"]["list_ratios"] = val_lists_ratio
                # self.save_train_params()
            else:
                data_config_check.append("val.list_ratios")

    def data_conf_by_tei_gb(self, data_config_check):
        self.state.nt_sel_tng_name = st.selectbox(
            "Choose a Groundtruth",
            tuple(self.tng.tngdict.keys()),
            tuple(self.tng.tngdict.keys()).index(self.state.nt_sel_tng_name) if self.state.nt_sel_tng_name else 0,
            key="nt_sel_tng",
            help="Choose a TEI NER Groundtruth which you want to use for training.",
        )
        ntd_name = self.tng.tngdict[self.state.nt_sel_tng_name][self.tng.tng_attr_tnm]["ntd"][self.ntd.ntd_attr_name]
        self.state.tng_trainer_params_json["scenario"]["data"]["tags"] = self.ntd.get_tag_filepath_to_ntdname(ntd_name)
        trainlistfilepath, devlistfilepath, testlistfilepath = self.tng.get_filepath_to_gt_lists(self.state.nt_sel_tng_name)
        self.state.tng_trainer_params_json["gen"]["train"]["lists"] = [trainlistfilepath]
        self.state.tng_trainer_params_json["gen"]["val"]["lists"] = [devlistfilepath]

    def workdir(self):
        if module_path != os.path.join(os.getcwd(), "tei_entity_enricher", "tei_entity_enricher"):
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
            self.state.tng_trainer_params_json = config_io.get_config("trainer_params.json")
        return 0

    def save_train_params(self):
        with remember_cwd():
            os.chdir(self._wd)
            config_io.set_config(self.state.tng_trainer_params_json)
        return 0
