import os
import yaml

class ConfigLoader:
    def __init__(self, config_directory, config_filename):
        self.config_path = os.path.join(config_directory, config_filename)

    def load_config(self):
        with open(self.config_path, 'r') as config_file:
            config = yaml.safe_load(config_file)
        return config


if __name__ == "__main__":
    # Использование класса ConfigLoader
    config_loader = ConfigLoader('../config/', 'node_config.yaml')
    config = config_loader.load_config()
    print(config.get("known_peers"))
