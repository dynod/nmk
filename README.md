# nmk - next-gen make-like build system

**nmk** is an alternative build system, designed following these simple requirements:
* both multi-platform and easy install - available as a python module
* shareable/reusable/factorized build logic between projects

## Usage

```
usage: nmk [-h] [-V] [-q | --info | -v] [--log-file L] [--no-logs] [-o O] [-p P] [task [task ...]]

Next-gen make-like build system

positional arguments:
  task               build task to execute

optional arguments:
  -h, --help         show this help message and exit
  -V, --version      show program's version number and exit

logging options:
  -q, --quiet        quiet mode (only warning/error messages)
  --info             default mode
  -v, --verbose      verbose mode (all messages, including debug ones)
  --log-file L       write logs to LOG_FILE (default: {out}/{time}-nmk.log)
  --no-logs          disable logging

output options:
  -o O, --output O   build output directory (default: out)

project options:
  -p P, --project P  project file (default: nmk.yml)
```
