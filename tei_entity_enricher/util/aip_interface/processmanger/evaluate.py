import logging
import sys, os

import streamlit as st

from tei_entity_enricher.util.aip_interface.processmanger.base import ProcessManagerBase

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names


@st.cache(allow_output_mutation=True)
def get_evaluate_process_manager(workdir):
    return EvaluateProcessManager(workdir=workdir, name="evaluate_process_manager")


class EvaluateProcessManager(ProcessManagerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_epoch: str = ""

    def clear_process(self):
        super().clear_process()
        self._current_epoch = ""

    def process_command_list(self):
        return [
            "tfaip-lav",
            "--export_dir",
            os.path.join(self._params.model,'best'),
            "--data.lists",
            self._params.current_test_list_path,
        ]

    def set_current_params(self,params):
        self._params=params


