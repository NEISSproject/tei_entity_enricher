import streamlit as st


class TEINERPostprocessing:
    def __init__(self, state, show_menu: bool = True):
        self.state = state
        if show_menu:
            self.show()

    def show(self):
        st.latex("\\text{\Huge{NER Postprocessing}}")
        # col1, col2 = st.beta_columns(2)
        # with col1:
        #     self.show_configs()
        # with col2:
        #     self.show_edit_environment()
        # self.show_test_environment()
