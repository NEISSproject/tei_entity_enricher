import logging
import os
import sys
from typing import Optional

import streamlit as st

from tei_entity_enricher.util.processmanger.base import ProcessManagerBase
from tei_entity_enricher.util.processmanger.ner_prediction_params import NERPredictionParams

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names
predict_option_json="Predict a JSON-File"
predict_option_tei="Predict Text of TEI-Files"
predict_option_single_tei="Predict a single TEI-File"
predict_option_tei_folder="Predict all TEI-Files of a folder"


@st.cache(allow_output_mutation=True)
def get_predict_process_manager(workdir, params):
    return PredictProcessManager(workdir=workdir, name="prediction_process_manager", params=params)


class PredictProcessManager(ProcessManagerBase):
    def __init__(self, params: NERPredictionParams, **kwargs):
        super().__init__(**kwargs)
        self._params: NERPredictionParams = params
        self._predict_script_path = os.path.join(
            self.work_dir, "tf2_neiss_nlp", "tfaip_scenario", "nlp", "ner", "scripts", "prediction_ner.py"
        )

    def process_command_list(self):
        return [
            "python",
            self._predict_script_path,
            "--export_dir",
            self._params.ner_model_dir,
            "--input_json",
            self._params.input_json_file,
            "--out",
            self._params.prediction_out_dir,
        ]
