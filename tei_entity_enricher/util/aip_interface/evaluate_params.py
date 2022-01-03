import os
from dataclasses import dataclass

from dataclasses_json import dataclass_json
import streamlit as st

from tei_entity_enricher.util.aip_interface.base_params import AIPBaseParams


@dataclass
@dataclass_json
class NEREvaluateParams(AIPBaseParams):
    current_test_list_path: str = ""

    def path_check(self, root, subdirs, files):
        pb_file_exist = os.path.isfile(os.path.join(root, "best", "serve", "saved_model.pb"))
        return True if pb_file_exist else False


@st.cache(allow_output_mutation=True)
def get_params() -> NEREvaluateParams:
    return NEREvaluateParams()
