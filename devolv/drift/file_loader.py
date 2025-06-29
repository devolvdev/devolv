import json
import yaml

def load_policy(path):
    with open(path, "r") as f:
        if path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        else:
            return json.load(f)
