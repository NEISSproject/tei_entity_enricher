import logging
import sys, os
import json
from queue import Empty

import streamlit as st

from tei_entity_enricher.util.aip_interface.processmanger.base import ProcessManagerBase
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.helper import remember_cwd

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names


@st.cache(allow_output_mutation=True)
def get_resume_process_manager(workdir):
    return ResumeProcessManager(workdir=workdir, name="resume_process_manager")


class ResumeProcessManager(ProcessManagerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_epoch: str = ""

    def clear_process(self):
        super().clear_process()
        self._current_epoch = ""

    def process_command_list(self):
        return [
            "tfaip-resume-training",
            self._params.model,
        ]

    def read_progress(self):
        try:
            while True:
                line = self.std_queue.get_nowait().decode("utf-8")  # or q.get(timeout=.1)
                if str(line).startswith("Epoch"):
                    self._current_epoch = line
                elif str(line).startswith("Field"):
                    pass
                elif line != "":
                    self._progress_content = line
                # logging.info(f"progress line: {self._progress_content}")
        except Empty:
            pass

        return f"{self._current_epoch}step:{self._progress_content}"

    def set_current_params(self,params):
        self._params=params

    def do_before_start_process(self):
        self._params.trainer_params_json["epochs"] = self._params.resume_to_epoch[self._params.model]
        self.save_train_params()

    def save_train_params(self):
        with open(os.path.join(self._params.model, "trainer_params.json"), "w") as fp:
            json.dump(self._params.trainer_params_json, fp, indent=2)
        return 0
