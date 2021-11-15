import os
import logging
from dataclasses import dataclass
from typing import Dict

from dataclasses_json import dataclass_json
import streamlit as st

from tei_entity_enricher.util.aip_interface.base_params import AIPBaseParams

logger = logging.getLogger(__name__)

allowed_hf_models = {
    "From Huggingface: German language model (deepset/gbert-base)": "deepset/gbert-base",
    "From Huggingface: English language model (bert-base-cased)": "bert-base-cased",
    "From Huggingface: Multilingual language model (bert-base-multilingual-cased)": "bert-base-multilingual-cased",
    "From Huggingface: French language model (Geotrend/bert-base-fr-cased)": "Geotrend/bert-base-fr-cased",
    "From Huggingface: Spanish language model (Geotrend/bert-base-es-cased)": "Geotrend/bert-base-es-cased",
}


@dataclass
@dataclass_json
class NERTrainerParams(AIPBaseParams):
    trainer_params_json: Dict = None
    nt_train_dir: str = None
    nt_val_dir: str = None
    is_hf_model: bool = False
    # nt_pretrained_model: str = None # moved to nt_train_params_json

    def path_check(self, root, subdirs, files):
        pb_file_exist = os.path.isfile(os.path.join(root, "encoder_only", "saved_model.pb"))
        return True if "encoder_only" in subdirs and pb_file_exist else False

    def scan_models(self, target_dir):
        possible_paths = []
        for root, subdirs, files in os.walk(target_dir):
            if self.path_check(root, subdirs, files):
                possible_paths.append(root)
        logger.debug(f"model possible_paths: {possible_paths}")
        self.possible_models = dict((os.path.relpath(x, target_dir), x) for x in possible_paths)
        self.possible_models.update(allowed_hf_models)
        logger.debug(f"model dict: {self.possible_models}")
        return 0 if possible_paths else -1

    def choose_model_widget(self, label="model", init=None, st_element=st):
        if init is not None and f"select_{label}" not in st.session_state and init in list(self.possible_models.keys()):
            st.session_state[f"select_{label}"] = init
        st_element.selectbox(
            label=f"Choose a {label}",
            options=tuple(self.possible_models.keys()),
            key=f"select_{label}",
            help=f"Choose a {label}, which you want to use.",
        )
        self.model = self.possible_models[st.session_state[f"select_{label}"]]
        if st.session_state[f"select_{label}"] in allowed_hf_models:
            self.is_hf_model = True
        else:
            self.is_hf_model = False


@st.cache(allow_output_mutation=True)
def get_params() -> NERTrainerParams:
    return NERTrainerParams()
