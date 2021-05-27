import logging
import os

import streamlit as st

logger = logging.getLogger(__name__)
module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_save_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

state_ok = r"\huge\color{green}\checkmark"
state_failed = r"\huge\color{red}X"
state_uncertain = r"\huge\color{orange}\bigcirc"

latex_color_list = ['red', 'green', 'blue', 'orange', 'purple', 'aqua', 'black', 'yellow', 'brown', 'gray']


def get_listoutput(list):
    output = ""
    for element in list:
        output += element + ', '
    if len(list) > 0:
        output = output[:-2]
    else:
        output = ""
    return output


def makedir_if_necessary(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)


def transform_arbitrary_text_to_markdown(text):
    return text.replace('\n', '\n\n').replace('*', '\*').replace('_', '\_').replace('{', '\{').replace('}', '\}') \
        .replace('(', '\(').replace(')', '\)').replace('[', '\[').replace(']', '\]').replace('#', '\#')


def clean_list_str(list_string: str):
    list_string = list_string.replace("'", "").replace('"', '')
    if list_string.startswith("["):
        list_string = list_string[1:]
    if list_string.endswith("]"):
        list_string = list_string[:-1]
    return list_string


def file_lists_entry_widget(list_param: list, name: str, help=None) -> list:
    """
    create a list text input field and checks if all files exist and sets the satus.
    :param list_param: a list variable handled by this wiget
    :param name: the name/unique key of the text input for streamlit
    :return: the list maybe modified by users input
    """
    # train_lists_str = clean_list_str(str(self.trainer_params_json["gen"]["train"]["lists"]))
    lists_str = clean_list_str(str(list_param))
    logger.debug(f"cleaned str: {lists_str}")

    lists_field, lists_state = st.beta_columns([10, 1])
    lists_field = lists_field.text_input(name, value=lists_str, help=help)

    if lists_field:
        lists_field = clean_list_str(lists_field)

    lists_list = [str(x).replace(" ", "") for x in lists_field.split(",")]
    ok = True if lists_list else False
    for list_name in lists_list:
        if not os.path.isfile(list_name):
            st.error(f"Can not find file: {list_name}")
            ok = False
    if ok:
        lists_state.latex(state_ok)
        return lists_list
    else:
        lists_state.latex(state_failed)
        return []


def numbers_lists_entry_widget(list_param: list, name: str, expect_amount: int = -1, expect_int: bool = False,
                               help=None) -> list:
    """
    create a list text input field and checks if expected amount and type matches if set.
    :param list_param: a list variable handled by this wiget
    :param name: the name/unique key of the text input for streamlit
    :param expect_amount: set >0 to activate
    :return: the list maybe modified by users input
    """
    # train_lists_str = clean_list_str(str(self.trainer_params_json["gen"]["train"]["lists"]))
    lists_str = clean_list_str(str(list_param))
    logger.debug(f"cleaned str: {lists_str}")

    lists_field, lists_state = st.beta_columns([10, 1])
    lists_field = lists_field.text_input(name, value=lists_str, help=help)
    if lists_field:
        lists_field = clean_list_str(lists_field)

    lists_list = [str(x).replace(" ", "") for x in lists_field.split(",")]
    ok = True if lists_list else False
    if expect_amount > 0 and len(lists_list) != expect_amount:
        ok = False
    if expect_int:
        for idx in range(len(lists_list)):
            try:
                lists_list[idx] = int(lists_list[idx])
            except:
                ok = False
    else:
        for idx in range(len(lists_list)):
            try:
                lists_list[idx] = float(lists_list[idx])
            except:
                ok = False

    if ok:
        lists_state.latex(state_ok)
        return lists_list
    else:
        lists_state.latex(state_failed)
        return []


def text_entry_with_check(string: str, name: str, check_fn: callable, help=None):
    string_field, string_state = st.beta_columns([10, 1])
    string_field = string_field.text_input(name, value=string, help=help)
    if check_fn(string_field):
        logger.info(f"Check {name}: ok: {string_field}")
        string_state.latex(state_ok)
        return string_field
    else:
        logger.warning(f"Check {name}: faild: {string_field}")
        string_state.latex(state_failed)
        return ""


def check_dir_ask_make(dir_string):
    if os.path.isdir(dir_string):
        return True
    else:
        logger.warning(f"Dir {dir_string} is not a directory.")
        st.warning(f"{dir_string} is not a directory")
        make_dir = st.button(f"Create dir: {dir_string}")
        if make_dir:
            os.makedirs(dir_string)
            st.experimental_rerun()
        return False


def model_dir_entry_widget(string_param: str, name: str, expect_saved_model: bool = False, ask_make_dir=False,
                           help=None) -> str:
    string_field, string_state = st.beta_columns([10, 1])
    string_field = string_field.text_input(name, value=string_param, help=help)
    ok = True
    if string_field:
        if not os.path.isdir(string_field):
            logger.warning(f"model_dir {name}: {string_field} is not a directory.")
            ok = False
            st.warning(f"{string_field} is not a directory")
            make_dir = st.button(f"Create dir: {string_field}")
            if make_dir:
                os.makedirs(string_field)
                st.experimental_rerun()
    if expect_saved_model and ok:
        ok = False
        test_path = str(string_field)
        for path_appendix in ["", "export", "additional", "encoder_only"]:
            test_path = os.path.join(string_field, path_appendix)
            if os.path.isfile(os.path.join(test_path, "saved_model.pb")):
                ok = True
                string_field = test_path
        if not ok:
            test_path = str(string_field)
            for path_appendix in ["", "best", "encoder_only"]:
                test_path = os.path.join(test_path, path_appendix)
                if os.path.isfile(os.path.join(test_path, "saved_model.pb")):
                    ok = True
                    string_field = test_path
    if ok:
        logger.info(f"Check {name}: ok: {string_field}")
        string_state.latex(state_ok)
        return string_field
    else:
        logger.warning(f"Check {name}: faild: {string_field}")
        string_state.latex(state_failed)
        return ""


def transform_arbitrary_text_to_latex(text):
    return text.replace('\n', '\n\n')
