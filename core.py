import json
from pathlib import Path
import subprocess

from config import ConfigJson


class GhostConverter:
    def __init__(self, incoming_file: str, output_file: str, type: str):
        """
        Compressing PDFs with GhostScript

        Args:
        input_file (str): Path to the original PDF file
        output_file (str, optional): Path to the compressed PDF file
        type (str): Mode used in the json file
        """
        self.incoming_file = incoming_file
        self.output_file = output_file
        self.type = type

        self.ghostscript = str(Path("bin\\gswin64c.exe").absolute())

        config_json = ConfigJson(Path("config.json"))
        self.config_json_path = config_json.determine_config_path()

    def load_config(self) -> dict:
        """
        Loads the JSON configuration file

        Returns:
        dict: Configuration parameters for each compression level
        """
        with open(self.config_json_path, 'r') as file:
            return json.load(file)


    def compress(self) -> list:
        """
        Compress a PDF
        Returns:
            list: a list of arguments
        """
        config = self.load_config()
        # Do not split the command, but directly create a list of arguments
        command_liste = []

        if config["base_args"]:
            base_args = config["base_args"]
        else:
            # base arguments
            base_args = [
                "-sDEVICE=pdfwrite",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dCompatibilityLevel=1.4"
            ]
        command_liste.extend(base_args)

        # Add the specific parameters from the configuration file
        for key, value in config[self.type].items():
            command_liste.append(f"-{key}={value}")

        # Add input and output files
        command_liste.append(f"-sOutputFile={self.output_file}")
        command_liste.append(self.incoming_file)

        return command_liste

    def launch(self) -> None:
        """
        Starts compressing the PDF
        """
        try:
            args = [self.ghostscript] + self.compress()
            # print(f"Order execution: {args}")
            process = subprocess.run(args, capture_output=True, text=True)

            if process.returncode != 0:
                print(f"Error GhostScript (code {process.returncode}):")
                print(f"Stdout: {process.stdout}")
                print(f"Stderr: {process.stderr}")
            # else:
                # print("Conversion successful")

        except Exception as e:
            print(f"Error running GhostScript: {e}")

# Example of use
if __name__ == "__main__":
    # Example to compress a file with different quality levels
    fichier_original = r"C:\temp\Gfsdffg.pdf"

    all_types = ["high", "medium", "low"]

    for type in all_types:
        convert = GhostConverter(fichier_original, f"C:\\temp\\exemple_{type}.pdf", type)
        convert.launch()



