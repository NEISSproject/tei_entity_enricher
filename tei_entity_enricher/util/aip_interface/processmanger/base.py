import os
import subprocess
import time
from multiprocessing import Queue
from queue import Empty
from threading import Thread
from typing import Optional

import streamlit as st

import logging

from streamlit_ace import st_ace
from streamlit_autorefresh import st_autorefresh
from tei_entity_enricher.util.helper import MessageType

logger = logging.getLogger(__name__)


class ProcessManagerBase:
    def __init__(self, workdir=os.getcwd(), verbose: int = 2, name="process_manager"):
        print("Manager is beeing Initialized")
        self.name: str = name
        self.work_dir: str = workdir
        self.verbose: int = verbose
        self.process: Optional[subprocess.Popen[str]] = None
        self.current_process_finished: bool = False
        self.messageType: str = None
        self.after_finish_message: str = None
        self.outs_str = ""
        self.errs_str = ""
        self.error_out = None
        self.std_queue: Optional[Queue] = None
        self.error_queue: Optional[Queue] = None
        self._log_content: str = ""
        self._progress_content: str = ""

    def message(self, message, level=MessageType.info, st_element=st):
        """level: info, error, warning, success"""
        fn_dict = {
            MessageType.info: (st_element.info, logger.info),
            MessageType.error: (st_element.error, logger.error),
            MessageType.warning: (st_element.warning, logger.warning),
            MessageType.success: (st_element.success, logger.info),
        }
        if level not in [MessageType.info, MessageType.error, MessageType.warning, MessageType.success]:
            msg = f"{message} was called with invalid level: {level}"
            logger.error(msg)
            if self.verbose >= 2:
                st.error(msg)
        if self.verbose >= 1:
            fn_dict[level][0](message)
        if self.verbose >= 2:
            fn_dict[level][1](message)

    def process_command_list(self):
        return ["echo", "Hello World!"]

    def do_before_start_process(self):
        # returns an error message if its execution failed otherwise it has to return None
        return None

    def do_after_finish_process(self):
        # returns a tupel of a messageType and message if there has to be displayed a special message otherwise it has to return None, None
        return None, None

    def force_process_start(self):
        st.session_state.force_process_start = True

    def start(self):
        if not self.process:
            # self.process = subprocess.Popen(
            #     ["bash", "ner_trainer/loop_sleep.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            # )
            error = self.do_before_start_process()
            self.current_process_finished = False
            self.messageType = None
            self.after_finish_message = None
            if error is None:
                self.process = subprocess.Popen(
                    args=self.process_command_list(),
                    cwd=self.work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                )
                self.std_queue = Queue()
                self.error_queue = Queue()
                t_std = Thread(target=self.enqueue_output, args=(self.process.stdout, self.std_queue))
                t_err = Thread(target=self.enqueue_output, args=(self.process.stderr, self.error_queue))
                t_std.daemon = True  # thread dies with the program
                t_std.start()
                t_err.daemon = True  # thread dies with the program
                t_err.start()
            else:
                self.message(f"process could not be started because an error occured: {error}", level=MessageType.error)
        else:
            self.message("Process is not empty, please clear process first.", level=MessageType.error)
            # error_msg = "Process is not empty, please clear process first."
            # if self.verbose >= 1:
            #     logger.error(error_msg)
            # if self.verbose >= 2:
            #     st.error(error_msg)

    def stop(self):
        self.process.terminate()
        return_code = None
        try:
            return_code = self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if st.button("Kill"):
                self.process.kill()
                return_code = self.process.wait(timeout=3)
        if return_code is not None:
            self.message("Process has stopped.", level=MessageType.info)

    def process_state(self, st_element=st):
        if "force_process_start" in st.session_state and st.session_state.force_process_start == True:
            st.session_state.force_process_start = False
            self.start()
        if self.process is not None:
            if self.process.poll() is None:
                self.message("running...", level=MessageType.info, st_element=st_element)
            elif self.process.poll() == 0:
                if not self.current_process_finished:
                    # run do_after_finish_process only once it its run is succesful
                    self.messageType, self.after_finish_message = self.do_after_finish_process()
                    self.current_process_finished = True
                    if self.messageType is not None:
                        self.message(
                            self.after_finish_message, self.messageType, st
                        )
                    else:
                        self.message("finished successful :-)", level=MessageType.success, st_element=st_element)
                else:
                    if self.messageType is not None:
                        self.message(
                            self.after_finish_message, self.messageType, st
                        )
                    else:
                        self.message("finished successful :-)", level=MessageType.success, st_element=st_element)
            else:
                self.message(f"process finished with error code: {self.process.poll()}", MessageType.error, st_element)
        else:
            self.message(f"process is empty", level=MessageType.info, st_element=st_element)

    def is_process_running(self):
        if self.process is not None and self.process.poll() is None:
            return True
        return False

    def clear_process(self):
        if self.process.poll() is not None:
            self._log_content = ""
            self._progress_content = ""
            self.process = None
        else:
            self.message("Stop process before clearing it.", "warning")

    def has_process(self):
        return True if self.process is not None else False

    def read_progress(self):
        try:
            while True:
                line = self.std_queue.get_nowait().decode("utf-8", errors="ignore")
                if line != "":
                    self._progress_content = line
        except Empty:
            time.sleep(1)
            pass

        return self._progress_content

    def log_content(self):
        try:
            while True:
                self._log_content += self.error_queue.get_nowait().decode("utf-8", errors="ignore")
        except Empty:
            time.sleep(1)
            pass
        return self._log_content

    @staticmethod
    def enqueue_output(out, queue):
        for line in iter(out.readline, b""):
            queue.put(line)
        out.close()

    def st_manager(self):
        with st.container():
            st.text(self.name)
            b1, b2, b3, b4, b5, process_status = st.columns([2, 2, 2, 2, 4, 6])
            b1.button("Start", on_click=self.force_process_start)
            b2.button("Stop", on_click=self.stop)
            b3.button("Clear", on_click=self.clear_process)
            b4.button("refresh")
            b5.checkbox(
                "Auto Refresh",
                key="auto_refresh_checkbox",
                value=False,
            )
            if st.session_state["auto_refresh_checkbox"] and self.is_process_running():
                count = st_autorefresh(interval=5000, limit=None, key="auto_refresh_instance")
            self.process_state(st_element=process_status)

            if self.has_process():
                with st.expander("Progress", expanded=True):
                    progress_str = self.read_progress()
                    logger.info(progress_str)
                    st.text(progress_str)
            if self.has_process():
                with st.expander("Log-file", expanded=True):
                    log_str = self.log_content()
                    st_ace(
                        log_str,
                        language="powershell",
                        auto_update=True,
                        readonly=True,
                        height=300,
                        wrap=True,
                        font_size=12,
                    )
        return 0
