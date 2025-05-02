from pathlib import Path
import os
import shutil


class ConfigJson:
    def __init__(self,config_json: Path):
        self.config_json = config_json

    def determine_config_path(self) -> Path:
        """
        Determines which configuration file to use:
        - Uses the local file if it is writable
        - Otherwise, copies the local file to AppData and uses that copy

        Returns:
        Path: Path to the configuration file to use
        """
        local_config = self.config_json.absolute()
        # Creates the path to the current user's AppData folder
        appdata_local_config = Path(os.environ['LOCALAPPDATA']) / 'DragDropPDF' / local_config.name

        if appdata_local_config.exists():
            print(f"appdata_local_config : {appdata_local_config}")
            return appdata_local_config
        elif local_config.exists():
            try:
                # Attempts to open the file in write mode to check permissions
                with open(local_config, 'a'):
                    print(f"local_config : {local_config}")
                    return local_config
            except PermissionError:
                # Checks if the folder in AppData exists, otherwise creates it
                appdata_dir = Path(appdata_local_config).parent
                appdata_dir.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copyfile(local_config, appdata_local_config)
                except (shutil.Error, IOError) as e:
                    raise Exception(f"An error occurred: {e}")
                else:
                    print(f"appdata_local_config : {appdata_local_config}")
                    return appdata_local_config
        else:
            raise FileNotFoundError(f"Critical error: The configuration file {local_config} does not exist.")

if __name__ == "__main__":
    config_json = ConfigJson(Path("config.json"))
    config_json_path = config_json.determine_config_path()
    print(str(config_json_path))

