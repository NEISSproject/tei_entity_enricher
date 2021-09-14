import logging
import os
import shutil
from typing import Optional

from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.menu.ner_trainer import NERTrainer
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_writer_map as tei_ner_writer_map
from tei_entity_enricher.util.aip_interface.prediction_params import NERPredictionParams, get_params
from tei_entity_enricher.util.aip_interface.processmanger.predict import (
    predict_option_tei,
    predict_option_json,
    predict_option_single_tei,
    predict_option_tei_folder,
    get_predict_process_manager,
)
from tei_entity_enricher.util.components import (
    small_file_selector,
    small_dir_selector,
    selectbox_widget,
    file_selector,
)
from tei_entity_enricher.util.helper import module_path, state_ok, local_save_path
from tei_entity_enricher.util.spacy_lm import lang_dict

import streamlit as st

logger = logging.getLogger(__name__)


class NERPrediction(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd: Optional[str] = None
        self._wd_ner_prediction = "ner_prediction"

        self.predict_conf_options = {
            predict_option_tei: self.select_tei_input_data,
            predict_option_json: self.select_json_input_data,
        }
        self.predict_conf_tei_input_options = {
            predict_option_single_tei: self.select_tei_file,
            predict_option_tei_folder: self.select_tei_folder,
        }

        if "predict_lang" not in st.session_state:
            st.session_state.predict_lang="German"

        self._check_list = []

        if self.show_menu:
            self.workdir()
            self.ner_trainer = NERTrainer(show_menu=False)
            self.ner_trainer.workdir()
            self.ner_trainer.load_trainer_params()
            self.tr = tei_reader.TEIReader(show_menu=False)
            self.tnw = tei_ner_writer_map.TEINERPredWriteMap(show_menu=False)
            self.show()

    @property
    def _params(self) -> NERPredictionParams:
        return get_params()

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

        predict_process_manager = get_predict_process_manager(workdir=self._wd)
        return_code = predict_process_manager.st_manager()
        if return_code != 0:
            return -1

        st.latex(state_ok)

    def select_model_dir(self):
        label = "ner model"
        target_dir = os.path.join(self._wd, "ner_trainer", "models_ner")
        if self._params.scan_models(target_dir) != 0:
            self._params.possible_models = {f"no {label} found": None}
            self._check_list.append(f"no {label} found")
        self._params.choose_model_widget(label)

    def select_output_dir(self):
        prediction_out_dir, prediction_out_dir_state = small_dir_selector(
            label="Folder for prediction output",
            value=self._wd_ner_prediction,
            key="ner_prediction_output_dir",
            help="Choose a directory with a trained NER model",
            return_state=True,
            ask_make=True,
        )
        if not prediction_out_dir_state:
            self._check_list.append("prediction output directory")
        else:
            self._params.prediction_out_dir = st.session_state.ner_prediction_output_dir

    def select_input_data(self):
        st.radio(
            "Prediction options",
            tuple(self.predict_conf_options.keys()),
            key="predict_conf_option",
            help="Choose an option to define what kind of Files you want to predict.",
        )
        self.predict_conf_options[st.session_state.predict_conf_option]()

    def select_json_input_data(self):
        init = str(
            self._params.input_json_file
            if self._params.input_json_file
            else os.path.join(self._wd_ner_prediction, "pred_input_example2.json")
        )

        target = f"Select input json-file: {self._params.input_json_file}"
        with st.expander(target, expanded=False):
            input_file = file_selector(folder_path=self._wd_ner_prediction, parent=target, init_file=init)

        def select():
            if input_file == "":
                self._check_list.append("input json-file")
            elif input_file:
                self._params.input_json_file = input_file

        st.button("select", on_click=select)

    def select_tei_input_data(self):
        np_tei_input_expander = st.expander("Select a TEI Prediction Configuration", expanded=False)
        with np_tei_input_expander:
            st.selectbox(
                label="Select a TEI Reader Config which should be used for the prediction!",
                options=list(self.tr.configdict.keys()),
                key="np_tei_pred_tr_name",
            )
            self._params.predict_tei_reader = self.tr.configdict[st.session_state.np_tei_pred_tr_name]
            st.selectbox(
                label="Select a TEI Prediction Writer Mapping which should be used for the prediction!",
                options=list(self.tnw.mappingdict.keys()),
                key="np_tei_pred_tnw_name",
            )
            self._params.predict_tei_write_map = self.tnw.mappingdict[st.session_state.np_tei_pred_tnw_name]
            st.selectbox(
                label="Select a language for the TEI-Files:",
                options=list(lang_dict.keys()),
                key="predict_lang",
                help="For Predicting entities the text of the TEI-Files has to be splitted into parts of sentences. For this sentence split you need to choose a language.",
            )
            st.radio(
                label="Input options",
                options=tuple(self.predict_conf_tei_input_options.keys()),
                key="predict_conf_tei_option",
                help="Choose an option to define if you want to predict a single TEI-File or all TEI-Files of a Folder.",
            )
            self.predict_conf_tei_input_options[st.session_state.predict_conf_tei_option]()

    def select_tei_file(self):
        input_tei_file, prediction_tei_file_state = small_file_selector(
            label="TEI-File to predict",
            key="input_tei_file",
            help="Choose a TEI-File whose text should be enriched with entities",
            return_state=True,
        )
        if prediction_tei_file_state != state_ok:
            self._check_list.append("TEI-File to predict")

    def select_tei_folder(self):
        input_tei_folder, prediction_tei_dir_state = small_dir_selector(
            label="Folder containing the TEI-Files to predict",
            key="input_tei_folder",
            help="Choose a directory containing TEI-Files whose text should be enriched with entities",
            return_state=True,
        )
        if prediction_tei_dir_state != state_ok:
            self._check_list.append("Folder containing the TEI-Files to predict")

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
