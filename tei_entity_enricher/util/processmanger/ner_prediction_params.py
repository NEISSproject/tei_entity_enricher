from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass
@dataclass_json
class NERPredictionParams:
    input_json_file: str = "pred_input_example1.json"
    ner_model_dir: str = "ner_trainer/models_ner/ner_germeval_default/best"
    prediction_out_dir: str = ""
