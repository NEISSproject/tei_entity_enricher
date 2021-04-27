import os

module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_listoutput(list):
    output = ""
    for element in list:
        output += element + ', '
    if len(list) > 0:
        output = output[:-2]
    else:
        output = ""
    return output


