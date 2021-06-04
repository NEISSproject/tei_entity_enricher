import streamlit as st


class TEIManPP:
    def __init__(self, state, show_menu=True):
        self.state = state
        if show_menu:
            self.show()

    def show(self):
        st.subheader("Manual TEI Postprocessing")
        man_tei = st.beta_expander("Manual TEI Postprocessing", expanded=True)
        with man_tei:
            st.write("Dummy")
