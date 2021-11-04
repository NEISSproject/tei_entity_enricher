import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json
import streamlit as st
from typing import Dict

from tei_entity_enricher.util.aip_interface.base_params import AIPBaseParams


@dataclass
@dataclass_json
class NERResumeParams(AIPBaseParams):
    trainer_params_json: Dict = None
    resume_to_epoch: Dict = None


    def path_check(self, root, subdirs, files):
        pb_file_exist = os.path.isfile(os.path.join(root, "best", "serve", "saved_model.pb"))
        return True if pb_file_exist else False


@st.cache(allow_output_mutation=True)
def get_params() -> NERResumeParams:
    return NERResumeParams()
