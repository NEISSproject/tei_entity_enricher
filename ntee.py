import streamlit as st
from SessionState import _get_state
from PIL import Image

def main():
    state = _get_state()
    pages = {
        "TEI Reader Config": teireader,
        "TEI NER Reader Config": teinerreader,
        "TEI NER Groundtruth Builder": gtbuilder,
        "TEI NER Writer Config": teinerwriter,
        "NER Trainer": nertrainer,
        "NER Prediction": nerprediction,
    }

    #Include NEISS Logo
    neiss_logo=Image.open('neiss_logo_nn_pentagon01b2.png')
    st.sidebar.image(neiss_logo)

    st.sidebar.title("NEISS TEI Entity Enricher")

    #Define sidebar as radiobuttons
    page = st.sidebar.radio("Main Menu", tuple(pages.keys()),0)

    # Display the selected page with the session state
    pages[page](state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()

def teireader(state):
    st.title("TEI Reader Config")
    state.input = st.text_input("Set input value.", state.input or "")
    st.subheader("Anforderungen für diesen Menüpunkt")
    st.markdown("Hier soll eine Konfiguration erstellt werden können, die definiert welcher Text aus den TEI-Files eines festen Formates ausgelesen werden soll (Gibt es Tags die ignoriert werden sollen oder kompletter inhalt des Body? etc...).")
    st.markdown("Diese Konfiguration muss abgespeichert und geladen werden können.")
    st.markdown("Eine TEI Reader config wird dann benötigt für die Menüpunkte: TEI NER Groundtruth Builder, TEI NER Writer Config,NER Prediction")

def teinerreader(state):
    st.title("TEI NER Reader Config")
    st.write("Page state:", state.page)
    st.subheader("Anforderungen für diesen Menüpunkt")
    st.markdown("Hier soll eine Konfiguration erstellt werden können, die definiert welche NER-Tags auf welche Tags (mit ggf. definierten Attributen) in den TEI Files eines festen Formates gehören.")
    st.markdown("Diese Konfiguration muss abgespeichert und geladen werden können.")
    st.markdown("Eine TEI Reader config wird dann benötigt für die Menüpunkte: TEI NER Groundtruth Builder, TEI NER Writer Config,NER Prediction")
    state.page

def gtbuilder(state):
    st.title("TEI NER Groundtruth Builder")
    st.write("Input state:", state.input)

    if st.button("Clear state"):
        state.clear()

def teinerwriter(state):
    st.title("TEI NER Writer Config")
    if st.button("Set Input to Konrad"):
        state.input="Konrad"

def nertrainer(state):
    st.title("NER Trainer")

def nerprediction(state):
    st.title("NER Prediction")
    file=st.file_uploader('Uploader')
    st.write(file.getvalue())


#def page_dashboard(state):
#    st.title(":chart_with_upwards_trend: Dashboard page")
#    display_state_values(state)


#def page_settings(state):
#    st.title(":wrench: Settings")
#    display_state_values(state)

#    st.write("---")
#    options = ["Hello", "World", "Goodbye"]
#    state.input = st.text_input("Set input value.", state.input or "")
#    state.slider = st.slider("Set slider value.", 1, 10, state.slider)
#    state.radio = st.radio("Set radio value.", options, options.index(state.radio) if state.radio else 0)
#    state.checkbox = st.checkbox("Set checkbox value.", state.checkbox)
#    state.selectbox = st.selectbox("Select value.", options, options.index(state.selectbox) if state.selectbox else 0)
#    state.multiselect = st.multiselect("Select value(s).", options, state.multiselect)

#    # Dynamic state assignments
#    for i in range(3):
#        key = f"State value {i}"
#        state[key] = st.slider(f"Set value {i}", 1, 10, state[key])


#def display_state_values(state):
#    st.write("Input state:", state.input)
#    st.write("Slider state:", state.slider)
#    st.write("Radio state:", state.radio)
#    st.write("Checkbox state:", state.checkbox)
#    st.write("Selectbox state:", state.selectbox)
#    st.write("Multiselect state:", state.multiselect)

#    for i in range(3):
#        st.write(f"Value {i}:", state[f"State value {i}"])

#    if st.button("Clear state"):
#        state.clear()

if __name__ == "__main__":
    main()
