import logging
import sys
from queue import Empty

import streamlit as st

from tei_entity_enricher.util.aip_interface.processmanger.base import ProcessManagerBase

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names


@st.cache(allow_output_mutation=True)
def get_train_process_manager(workdir):
    return TrainProcessManager(workdir=workdir, name="train_process_manager")


class TrainProcessManager(ProcessManagerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_epoch: str = ""

    def clear_process(self):
        super().clear_process()
        self._current_epoch = ""

    def process_command_list(self):
        return [
            "tfaip-train-from-params",
            "trainer_params.json",
            "--trainer.progress_bar_mode=2",
            "--trainer.progbar_delta_time=1",
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
