import logging
import subprocess
import sys
import tempfile
from multiprocessing import Queue
from queue import Empty
from threading import Thread
from time import sleep

import streamlit as st


logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names


@st.cache(allow_output_mutation=True)
def get_manager(workdir):
    return TrainManager(workdir)


class TrainManager:
    def __init__(self, work_dir):
        print("Manager is beeing Initialized")
        self.trainer_params = None
        self.work_dir = work_dir
        self.process: subprocess.Popen[str] = None
        self.outs_str = ""
        self.errs_str = ""
        self.error_out = None
        self.std_queue: Queue = None
        self.error_queue: Queue = None
        self._log_content: str = ""
        self._progress_content: str = ""
        self._current_epoch: str = ""

    def set_params(self, trainer_params):
        self.trainer_params = trainer_params

    def start(self):
        if not self.process:
            # self.process = subprocess.Popen(
            #     ["bash", "ner_trainer/loop_sleep.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            # )
            self.process = subprocess.Popen(
                [
                    "tfaip-train-from-params",
                    "trainer_params.json",
                    "--trainer.progress_bar_mode=2",
                    "--trainer.progbar_delta_time=1",
                ],
                cwd=self.work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            self.std_queue = Queue()
            self.error_queue = Queue()
            t_std = Thread(target=enqueue_output, args=(self.process.stdout, self.std_queue))
            t_err = Thread(target=enqueue_output, args=(self.process.stderr, self.error_queue))
            t_std.daemon = True  # thread dies with the program
            t_std.start()
            t_err.daemon = True  # thread dies with the program
            t_err.start()
        else:
            error_msg = "Process is not empty, please clear process first."
            logger.error(error_msg)
            st.error(error_msg)

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
            st.info("Process has stopped.")

    def process_state(self, st_element=st):
        if self.process is not None:
            if self.process.poll() is None:
                st_element.info("running...")
            elif self.process.poll() == 0:
                st_element.success("finished successful :-)")
            else:
                st_element.error(f"process finished with error code: {self.process.poll()}")
        else:
            st_element.info(f"process is empty")

    def clear_process(self):
        if self.process.poll() is not None:
            self._log_content = ""
            self._current_epoch = ""
            self._progress_content = ""
            self.process = None
        else:
            st.warning("Stop process before clearing it.")

    def has_process(self):
        return True if self.process is not None else False

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

    def log_content(self):
        try:
            while True:
                self._log_content += self.error_queue.get_nowait().decode("utf-8")  # or q.get(timeout=.1)
                # logging.info(f"log content: {self._log_content}")
        except Empty:
            pass
        return self._log_content


def main():
    # manager = Manager()
    manager = get_manager()
    selected = st.selectbox("Dummy", [1, 23, 4])
    if st.button("add"):
        manager.do_smth(selected)


# class StdoutQueue(Queue):
#     def __init__(self,*args,**kwargs):
#         Queue.__init__(self,*args,**kwargs)
#
#     def write(self,msg):
#         self.put(msg)
#
#     def flush(self):
#         sys.__stdout__.flush()


def enqueue_output(out, queue):
    for line in iter(out.readline, b""):
        queue.put(line)
    out.close()


if __name__ == "__main__":
    main()
