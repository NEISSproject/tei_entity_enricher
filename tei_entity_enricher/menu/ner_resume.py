import logging
import os
import shutil
from typing import Optional

import streamlit as st

from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.util.aip_interface.resume_params import NERResumeParams, get_params
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.helper import (
    module_path,
    state_ok,
    remember_cwd,
    menu_NER_resume,
)
from tei_entity_enricher.util.aip_interface.processmanger.resume import get_resume_process_manager

logger = logging.getLogger(__name__)


class NERResumer(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd: Optional[str] = None
        # self.training_state = None
        self._data_config_check = []
        self.selected_ner_model = None
        self.resume_process_manager = None
        self._check_list = []

        if self.show_menu:
            self.workdir()
            self.show()

    @property
    def _params(self) -> NERResumeParams:
        return get_params()

    def show_resume_config_options(self):
        self.select_model_dir()
        if self._params.model and os.path.isfile(os.path.join(self._params.model, "trainer_params.json")):
            self._params.trainer_params_json = config_io.get_config(
                os.path.join(self._params.model, "trainer_params.json")
            )
            st.info(
                f'The model {os.path.basename(self._params.model)} was already trained for {self._params.trainer_params_json["current_epoch"]} epochs. The highest entity-wise F1 score obtained so far from the best epoch on the validation set was {self._params.trainer_params_json["early_stopping"]["current"]}.'
            )
            if self._params.resume_to_epoch is None:
                self._params.resume_to_epoch={}
            if self._params.model not in self._params.resume_to_epoch.keys():
                self._params.resume_to_epoch[self._params.model] = self._params.trainer_params_json["epochs"]
            if self._params.trainer_params_json["current_epoch"] + 1 > self._params.resume_to_epoch[self._params.model]:
                self._params.resume_to_epoch[self._params.model] = self._params.trainer_params_json["current_epoch"] + 1
            self._params.resume_to_epoch[self._params.model] = st.number_input(
                label="Resume training until epoch",
                min_value=self._params.trainer_params_json["current_epoch"] + 1,
                value=self._params.resume_to_epoch[self._params.model],
                step=1,
                help="Define the epoch up to which the training should be continued.",
            )

    def show(self):
        st.latex("\\text{\Huge{" + menu_NER_resume + "}}")

        self.show_resume_config_options()

        if self._check_list:
            st.error(f"Pre-configuration failed. Please correct: {', '.join(self._check_list)}!")
            return -1
        if self._resume_manager() != 0:
            return -1

        st.latex(state_ok)

    def _resume_manager(self):
        self.resume_process_manager = get_resume_process_manager(workdir=self._wd)
        self.resume_process_manager.set_current_params(self._params)
        return_code = self.resume_process_manager.st_manager()
        return return_code

    def select_model_dir(self):
        label = "NER Model to resume"
        target_dir = os.path.join(self._wd, "models_ner")
        if self._params.scan_models(target_dir) != 0:
            self._params.possible_models = {f"no {label} found": None}
            self._check_list.append(f"no {label} found")
        self._params.choose_model_widget(label)
        # st.write(self._params.model)

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

        return 0
