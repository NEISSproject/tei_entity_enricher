import pandas as pd
import streamlit as st
from st_aggrid import AgGrid
import numpy as np


def editable_single_column_table(
    entry_list, key, head, openentrys=100, height=150, width=1
):
    response = AgGrid(
        pd.DataFrame({head: entry_list + [""] * openentrys}),  # input_dataframe,
        height=height,
        editable=True,
        sortable=False,
        filter=False,
        resizable=True,
        defaultWidth=width,
        fit_columns_on_grid_load=True,
        key=key,
    )
    st.info(
        "Edit the table by double-click in it and press Enter after changing a cell."
    )
    returnlist = []
    if "data" in response:
        all_list = list(response["data"].to_dict()[head].values())
        for element in all_list:
            if element != "" and element is not None:
                returnlist.append(element)
    return returnlist


def editable_multi_column_table(entry_dict, key, openentrys=100, height=150, width=1):
    in_data = entry_dict.copy()
    max_len = openentrys
    for entry_dict_key in in_data.keys():
        if len(in_data[entry_dict_key]) > max_len:
            max_len = len(in_data[entry_dict_key])
    for entry_dict_key in in_data.keys():
        # in_data[entry_dict_key]=in_data[entry_dict_key] + [''] * (max_len-len(in_data[entry_dict_key]))
        # in_data[entry_dict_key].extend([''] * (max_len-len(in_data[entry_dict_key])))
        keylist = in_data[entry_dict_key].copy()
        keylist.extend([""] * (max_len - len(in_data[entry_dict_key])))
        in_data[entry_dict_key] = keylist

    response = AgGrid(
        pd.DataFrame(in_data),  # input_dataframe,
        height=height,
        editable=True,
        sortable=False,
        filter=False,
        resizable=True,
        defaultWidth=width,
        fit_columns_on_grid_load=True,
        key=key,
    )
    st.info(
        "Edit the table by double-click in it and press Enter after changing a cell."
    )
    if "data" in response:
        answer_dict = response["data"].to_dict()
        returndict = {}
        for key in answer_dict:
            answer_dict[key] = list(answer_dict[key].values())
            returndict[key] = []
        for i in range(max_len):
            needed = False
            for key in answer_dict:
                if answer_dict[key][i] is not None and answer_dict[key][i] != "":
                    needed = True
            if needed:
                for key in answer_dict:
                    returndict[key].append(answer_dict[key][i])
        return returndict
    return entry_dict
