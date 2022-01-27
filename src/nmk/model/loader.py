from argparse import Namespace
from pathlib import Path
from typing import List

from nmk.model.items import NmkModelFile

# Loading error prefix
ERROR_PREFIX = "While loading "


class NmkModel:
    def __init__(self, args: Namespace):
        # Prepare repo cache
        self.repo_cache: Path = args.cache / "cache"

        # Iterate recursively on model files
        self.files = {}
        try:
            self.load_model([NmkModelFile(args.project, self.repo_cache)])
        except Exception as e:
            self.raise_prettier_error(e, args.project)

    def load_model(self, files: List[NmkModelFile], ref_from: List[str] = None):
        # Remember known files
        self.files.update({str(f.file): f for f in files})

        # Iterate on loaded files
        for file in files:
            try:
                # Recursively load model from new references
                new_ref = (ref_from if ref_from is not None else []) + [f" --> referenced from {file.file}"]
                new_files = []
                for ref_file_path in filter(lambda f: f not in self.files, file.refs):
                    try:
                        new_files.append(NmkModelFile(ref_file_path, file.repo_cache))
                    except Exception as e:
                        self.raise_prettier_error(e, ref_file_path, new_ref)
                self.load_model(new_files, new_ref)
            except Exception as e:
                # Add details to loading error
                self.raise_prettier_error(e, file.file, ref_from)

    def raise_prettier_error(self, e: Exception, file_path: Path, ref_from: List[str] = None):
        if str(e).startswith(ERROR_PREFIX):
            raise e
        raise Exception(f"{ERROR_PREFIX}{file_path}: {e}" + (("\n" + "\n".join(ref_from)) if ref_from is not None else "")).with_traceback(e.__traceback__)
