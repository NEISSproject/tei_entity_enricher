import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json
import streamlit as st

from tei_entity_enricher.util.aip_interface.base_params import AIPBaseParams


@dataclass
@dataclass_json
class NERPredictionParams(AIPBaseParams):
    input_json_file: str = "pred_input_example1.json"
    ner_model_dir: str = "ner_trainer/models_ner/ner_germeval_default/best"
    prediction_out_dir: str = ""
    predict_conf_option: str = ""
    predict_conf_tei_option: str = ""
    predict_tei_reader: dict = None
    predict_tei_write_map: dict = None
    predict_lang: str = "German"
    input_tei_file: str = ""
    input_tei_folder: str = ""

    def path_check(self, root, subdirs, files):
        pb_file_exist = os.path.isfile(os.path.join(root, "export", "serve", "saved_model.pb"))
        return True if "export" in subdirs and pb_file_exist else False


@st.cache(allow_output_mutation=True)
def get_params() -> NERPredictionParams:
    return NERPredictionParams()
