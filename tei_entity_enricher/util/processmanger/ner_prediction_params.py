import streamlit as st
from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass
@dataclass_json
class NERPredictionParams:
    input_json_file: str = "pred_input_example1.json"
    ner_model_dir: str = "ner_trainer/models_ner/ner_germeval_default/best"
    prediction_out_dir: str = ""
    predict_conf_option: str = ""
    predict_conf_tei_option: str = ""
    predict_tei_reader: dict = None
    predict_tei_write_map: dict = None
    input_tei_file: str = ""
    input_tei_folder: str = ""

@st.cache(allow_output_mutation=True)
def get_params() -> NERPredictionParams:
    return NERPredictionParams()
