import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode


def editable_table(entry_list, key, head, openentrys=100, height=150, width=1):
    response = AgGrid(
        pd.DataFrame({head: entry_list + [''] * openentrys}),  # input_dataframe,
        height=height,
        editable=True,
        sortable=False,
        filter=False,
        resizable=True,
        defaultWidth=width,
        fit_columns_on_grid_load=True,
        key=key)
    st.info('Edit the table by double-click in it and press Enter after changing a cell.')
    returnlist = []
    if 'data' in response:
        all_list = list(response['data'].to_dict()[head].values())
        for element in all_list:
            if element != '' and element is not None:
                returnlist.append(element)
    return returnlist
