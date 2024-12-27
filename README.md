# nmk - next-gen make-like build system

<!-- NMK-BADGES-BEGIN -->
[![License: MIT License](https://img.shields.io/github/license/dynod/nmk)](https://github.com/dynod/nmk/blob/main/LICENSE)
[![Checks](https://img.shields.io/github/actions/workflow/status/dynod/nmk/build.yml?branch=main&label=build%20%26%20u.t.)](https://github.com/dynod/nmk/actions?query=branch%3Amain)
[![Issues](https://img.shields.io/github/issues-search/dynod/nmk?label=issues&query=is%3Aopen+is%3Aissue)](https://github.com/dynod/nmk/issues?q=is%3Aopen+is%3Aissue)
[![Supported python versions](https://img.shields.io/badge/python-3.9%20--%203.13-blue)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/nmk)](https://pypi.org/project/nmk/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://astral.sh/ruff)
[![Code coverage](https://img.shields.io/codecov/c/github/dynod/nmk)](https://app.codecov.io/gh/dynod/nmk)
[![Documentation Status](https://readthedocs.org/projects/nmk/badge/?version=stable)](https://nmk.readthedocs.io/)
<!-- NMK-BADGES-END -->

**`nmk`** is an alternative build system, designed following these simple requirements:
* both multi-platform and easy install - available as a python module
* shareable/reusable/factorized build logic between projects
* language agnostic - each language support is done through plugins

## Usage

In an **`nmk`** project, just execute:
```shell
$ ./buildenv.sh # Load the build environment
$ nmk           # Trigger the nmk build!
```

## Documentation

For the full **`nmk`** documentation, see https://nmk.readthedocs.io/
