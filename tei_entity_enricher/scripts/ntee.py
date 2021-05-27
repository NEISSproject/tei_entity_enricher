import argparse
import logging
import subprocess
import os
import sys

import tei_entity_enricher.menu.main as main_menu

this_file = os.path.abspath(__file__)

logging.basicConfig(level="INFO")


def run():
    args = sys.argv
    subprocess.call(
        [
            "streamlit",
            "run",
            this_file,
            "--browser.gatherUsageStats",
            "false",
            "--logger.messageFormat",
            "%(asctime)s %(levelname) -7s %(name)s: %(message)s",
            *args,
        ]
    )


def main():
    parser = argparse.ArgumentParser(description="The n-tee app")

    parser.add_argument(
        "--start_state",
        default=0,
        type=int,
        help="set start state/tab: 0-tei_reader, 1-ner_task_def, 2-tei_ner_map, "
        "3-gt_builder, 4-tei_ner_writer, 5-ner_trainer, 6-ner_prediction",
    )

    args, unknown = parser.parse_known_args()
    main_menu.Main(args)


if __name__ == "__main__":
    main()
