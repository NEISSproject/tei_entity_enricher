import logging
import os
import shutil
from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json
from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.menu.ner_trainer import NERTrainer
from tei_entity_enricher.util.components import small_dir_selector, file_selector_expander
from tei_entity_enricher.util.helper import remember_cwd, module_path, state_ok
from tei_entity_enricher.util.processmanger.ner_prediction_params import NERPredictionParams
from tei_entity_enricher.util.processmanger.predict import get_predict_process_manager
import streamlit as st

logger = logging.getLogger(__name__)


class NERPrediction(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd: Optional[str] = None
        self._wd_ner_prediction = "ner_prediction"

        if not self.state.ner_prediction_params:
            self.state.ner_prediction_params = NERPredictionParams()

        self._check_list = []

        if self.show_menu:
            self.workdir()
            self.ner_trainer = NERTrainer(state=self.state, show_menu=False)
            self.ner_trainer.workdir()
            self.ner_trainer.load_trainer_params()
            self.show()

    @property
    def ner_prediction_params(self) -> NERPredictionParams:
        return self.state.ner_prediction_params

    def check(self, **kwargs):
        # Todo implement
        return True

    def show(self, **kwargs):
        self.select_model_dir()

        self.select_output_dir()

        self.select_input_data()

        if self._check_list:
            st.error(f"Pre-configuration failed. Please correct: {', '.join(self._check_list)}!")
            return -1

        print("state", self.state.ner_prediction_params)
        print("self", self.ner_prediction_params)

        predict_process_manager = get_predict_process_manager(workdir=self._wd, params=self.ner_prediction_params)
        return_code = predict_process_manager.st_manager()
        if return_code != 0:
            return -1

        st.latex(state_ok)

    def select_model_dir(self):
        ner_model_dir, ner_model_dir_state = small_dir_selector(
            state=self.state,
            label="Folder with NER model",
            value=self.ner_prediction_params.ner_model_dir if self.ner_prediction_params.ner_model_dir else self._wd,
            key="ner_prediction_ner_model_dir",
            help="Choose a directory with a trained NER model",
            return_state=True,
        )
        if not ner_model_dir_state:
            self._check_list.append("NER model")
        else:
            self.ner_prediction_params.ner_model_dir = ner_model_dir

    def select_output_dir(self):
        prediction_out_dir, prediction_out_dir_state = small_dir_selector(
            state=self.state,
            label="Folder for prediction output",
            value=self.ner_prediction_params.prediction_out_dir
            if self.ner_prediction_params.prediction_out_dir
            else self._wd_ner_prediction,
            key="ner_prediction_output_dir",
            help="Choose a directory with a trained NER model",
            return_state=True,
        )
        if not prediction_out_dir_state:
            self._check_list.append("prediction output directory")
        else:
            self.ner_prediction_params.prediction_out_dir = prediction_out_dir

    def select_input_data(self):
        input_file = file_selector_expander(
            folder_path=self._wd_ner_prediction,
            target=f"Select input json-file: {self.ner_prediction_params.input_json_file}",
            init_file=self.ner_prediction_params.input_json_file
            if self.ner_prediction_params.input_json_file
            else os.path.join(self._wd_ner_prediction, "pred_input_example2.json"),
        )
        if input_file == "":
            self._check_list.append("input json-file")
        else:
            self.ner_prediction_params.input_json_file = input_file

    def workdir(self):
        if module_path.lower() != os.path.join(os.getcwd(), "tei_entity_enricher", "tei_entity_enricher").lower():
            if self.show_menu:
                st.error("Please run ntee-start from the directory which contains the git repos 'tei_entity_enricher'.")
            else:
                logging.error(
                    "Please run ntee-start from the directory which contains the git repos 'tei_entity_enricher'."
                )
            return -1
        self._wd = os.getcwd()

        if not os.path.isdir(self._wd_ner_prediction):
            st.error(
                f"The working directory for ner_prediction does not exist yet. "
                f"Do you want to create the directory: {self._wd_ner_prediction}?"
            )
            if st.button(f"Create: {self._wd_ner_prediction}"):
                if not os.path.isdir(self._wd_ner_prediction):
                    os.makedirs(self._wd_ner_prediction)
            return -1

        if not os.path.isfile(os.path.join(self._wd_ner_prediction, "pred_input_example1.json")):
            template_dir = os.path.join(module_path, "templates", "prediction", "templates")
            shutil.copy(os.path.join(template_dir, "pred_input_example1.json"), self._wd_ner_prediction)
            shutil.copy(os.path.join(template_dir, "pred_input_example2.json"), self._wd_ner_prediction)
        return 0
