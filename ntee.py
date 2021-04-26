import streamlit as st
from TEIEntityEnricher.SessionState import _get_state
from PIL import Image
import os
import TEIEntityEnricher.menu_tei_reader as tr
import TEIEntityEnricher.menu_ner_task_def as ntd
import TEIEntityEnricher.menu_tei_ner_map as tnm

def main():
    st.set_page_config(layout='wide') #Hiermit kann man die ganze Breite des Bildschirms ausschöpfen
    state = _get_state()
    pages = {
        "TEI Reader Config": teireader,
        "NER Task Entity Definition": nertaskdef,
        "TEI NER Entity Mapping": teinermap,
        "TEI NER Groundtruth Builder": gtbuilder,
        "TEI NER Writer Config": teinerwriter,
        "NER Trainer": nertrainer,
        "NER Prediction": nerprediction,
    }
    st.sidebar.latex('\\text{\Huge{N-TEE}}')
    st.sidebar.latex('\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}')

    #Include NEISS Logo
    neiss_logo=Image.open('TEIEntityEnricher/neiss_logo_nn_pentagon01b2.png')
    st.sidebar.image(neiss_logo)


    #Define sidebar as radiobuttons
    state.page = st.sidebar.radio("Main Menu", tuple(pages.keys()),tuple(pages.keys()).index(state.page) if state.page else 0)

    # Display the selected page with the session state
    pages[state.page](state)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()

def teireader(state):
    tr.Menu_tei_reader(state)

def nertaskdef(state):
    ntd.Menu_ner_task_def(state)

def teinermap(state):
    tnm.Menu_ner_tei_map(state)

def gtbuilder(state):
    st.latex('\\text{\Huge{TEI NER Groundtruth Builder}}')
    st.write("Input state:", state.input)

    if st.button("Clear state"):
        state.input=None
        st.experimental_rerun()

def teinerwriter(state):
    st.latex('\\text{\Huge{TEI NER Writer Config}}')
    if st.button("Set Input to Konrad"):
        state.input="Konrad"

def nertrainer(state):
    st.latex('\\text{\Huge{NER Trainer}}')
    state.input = st.text_input("Set input value.", state.input or "")
    st.write("Page state:", state.page)
    if st.button("Jump to Pred"):
        state.page="NER Prediction"
        st.experimental_rerun()

def nerprediction(state):
    st.latex('\\text{\Huge{NER Prediction}}')
    state.folderPath = st.text_input('Enter folder path:')
    if state.folderPath:
        fileslist = os.listdir(state.folderPath)
    else:
        fileslist=[]  # Hack to clear list if the user clears the cache and reloads the page
        st.info("Select a folder.")
    # And within an expander
    my_expander = st.beta_expander("Selected Files", expanded=True)
    with my_expander:
        st.table(fileslist)



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
