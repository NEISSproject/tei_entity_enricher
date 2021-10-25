import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json
import streamlit as st

from tei_entity_enricher.util.aip_interface.base_params import AIPBaseParams


@dataclass
@dataclass_json
class NERPredictionParams(AIPBaseParams):
    input_json_file: str = "pred_input_example1.json"
    prediction_out_dir: str = ""
    predict_tei_reader: dict = None
    predict_tei_write_map: dict = None

    # def path_check(self, root, subdirs, files):
    #     pb_file_exist = os.path.isfile(os.path.join(root, "export", "serve", "saved_model.pb"))
    #     pb_best_file_exist = os.path.isfile(os.path.join(root, "best", "serve", "saved_model.pb"))
    #     return True if ("export" in subdirs or "best" in subdirs) and (pb_file_exist or pb_best_file_exist) else False
    #
    def path_check(self, root, subdirs, files):
        pb_file_exist = os.path.isfile(os.path.join(root, "serve", "saved_model.pb"))
        is_export_or_best = os.path.basename(root) in ["export", "best"]
        return True if pb_file_exist and is_export_or_best else False


@st.cache(allow_output_mutation=True)
def get_params() -> NERPredictionParams:
    return NERPredictionParams()
