import logging
import os
import sys
from typing import Optional

import streamlit as st

from tei_entity_enricher.util.processmanger.base import ProcessManagerBase

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names


@st.cache(allow_output_mutation=True)
def get_predict_process_manager(workdir):
    return PredictProcessManager(workdir)


class PredictProcessManager(ProcessManagerBase):
    def __init__(self, work_dir):
        super().__init__(work_dir)
        self._ner_model_directory: Optional[str] = None
        self._prediction_out_directory: Optional[str] = None
        self._predict_script_path = os.path.join(
            os.path.dirname(work_dir), "tf2_neiss_nlp", "tfaip_scenario", "nlp", "ner", "scripts", "prediction_ner.py"
        )
        self._input_json: Optional[str] = None

    def process_command_list(self):
        return [
            "python",
            self._predict_script_path,
            "--export_dir",
            "--input_json",
            self._input_json,
            self._ner_model_directory,
            "--out",
            self._prediction_out_directory,
        ]
