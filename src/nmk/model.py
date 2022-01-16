from argparse import Namespace
from pathlib import Path

import jsonschema
import yaml


class NmkModel:
    def __init__(self, args: Namespace):
        # Get project from args
        self.project_file: Path = args.project
        assert self.project_file.is_file(), f"Project file not found: {self.project_file}"

        # Load YAML model
        try:
            with self.project_file.open() as f:
                self.model = yaml.full_load(f)
        except Exception as e:
            raise Exception(f"Project '{self.project_file}' is malformed: {e}")

        # Validate model against grammar
        try:
            with (Path(__file__).parent / "model.yml").open() as f:
                schema = yaml.full_load(f)
            jsonschema.validate(self.model, schema)
        except Exception as e:
            raise Exception(f"Project '{self.project_file}' contains invalid data: {e}")
