import os

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
local_save_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def get_listoutput(list):
    output = ""
    for element in list:
        output += element + ', '
    if len(list) > 0:
        output = output[:-2]
    else:
        output = ""
    return output

def transform_arbitrary_text_to_markdown(text):
    return text.replace('\n','\n\n').replace('*','\*').replace('_','\_').replace('{','\{').replace('}','\}').replace('(','\(').replace(')','\)').replace('[','\[').replace(']','\]').replace('#','\#')
