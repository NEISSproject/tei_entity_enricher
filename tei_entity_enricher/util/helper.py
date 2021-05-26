import os

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_save_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

state_ok = r"\huge\color{green}\checkmark"
state_failed = r"\huge\color{red}X"
state_uncertain = r"\huge\color{orange}\bigcirc"

latex_color_list=['red','green','blue','orange','purple','aqua','black','yellow','brown','gray']

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
        os.makedirs(directory)

def transform_arbitrary_text_to_markdown(text):
    return text.replace('\n','\n\n').replace('*','\*').replace('_','\_').replace('{','\{').replace('}','\}').replace('(','\(').replace(')','\)').replace('[','\[').replace(']','\]').replace('#','\#')

def transform_arbitrary_text_to_latex(text):
    return text.replace('\n','\n\n')
