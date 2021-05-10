import logging
import subprocess
import os
import tei_entity_enricher.menu.main as main_menu

this_file = os.path.abspath(__file__)

# logging.basicConfig(level="INFO")

def run():
    subprocess.call(["streamlit", "run", this_file, "--browser.gatherUsageStats", "false"])


def main():
    main_menu.Main()


if __name__ == "__main__":
    main()
