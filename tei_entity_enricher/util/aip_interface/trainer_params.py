import os
from dataclasses import dataclass
from typing import Dict

from dataclasses_json import dataclass_json
import streamlit as st

from tei_entity_enricher.util.aip_interface.base_params import AIPBaseParams


@dataclass
@dataclass_json
class NERTrainerParams(AIPBaseParams):
    trainer_params_json: Dict = None
    nt_train_option: str = None
    nt_sel_ntd_name: str = None
    nt_train_list_option: str = None
    nt_sel_tng_name: str = None
    nt_train_dir: str = None
    nt_val_dir: str = None
    # nt_pretrained_model: str = None # moved to nt_train_params_json
    nt_output_dir: str = None

    def path_check(self, root, subdirs, files):
        pb_file_exist = os.path.isfile(os.path.join(root, "encoder_only", "saved_model.pb"))
        return True if "encoder_only" in subdirs and pb_file_exist else False


@st.cache(allow_output_mutation=True)
def get_params() -> NERTrainerParams:
    return NERTrainerParams()
