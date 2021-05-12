import subprocess

import streamlit as st


@st.cache(allow_output_mutation=True)
def get_manager():
    return TrainManager()


class TrainManager:
    def __init__(self):
        print("Manager is beeing Initialized")
        self.trainer_params = None
        self.process = None

    def set_params(self, trainer_params):
        self.trainer_params = trainer_params

    def start(self):
        if not self.process:
            # self.process = subprocess.Popen(["sh", "loop_sleep.sh"])
            self.process = subprocess.Popen(["sh", "count_sleep.sh"])

    def terminate(self):
        self.process.terminate()

    def clear_process(self):
        self.process = None


def main():
    # manager = Manager()
    manager = get_manager()
    selected = st.selectbox("Dummy", [1, 23, 4])
    if st.button("add"):
        manager.do_smth(selected)


if __name__ == "__main__":
    main()
