# Usage

This page describes basic **`nmk`** usage and the supported command line options.

Use **`nmk -h`** to get live help about these options in the terminal.

```
user@host:~$ $ nmk -h
usage: nmk [-h] [-V] [-q | --info | -v] [--log-file L] [--no-logs] [--log-prefix PREFIX] [-r R] [--no-cache] [-p P] [--config JSON|K=V] [--print K] [--dry-run] [--force]
           [--skip SKIPPED_TASKS]
           [task ...]

Next-gen make-like build system

positional arguments:
  task                  build task to execute

options:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit

logging options:
  -q, --quiet           quiet mode (only warning/error messages)
  --info                default mode
  -v, --verbose         verbose mode (all messages, including debug ones)
  --log-file L          write logs to L (default: {ROOTDIR}/.nmk/nmk.log)
  --no-logs             disable logging
  --log-prefix PREFIX   prefix for all log messages

root folder options:
  -r R, --root R        root folder (default: virtual env parent)
  --no-cache            clear cache before resolving references

project options:
  -p P, --project P     project file (default: nmk.yml)

config options:
  --config JSON|K=V     contribute or override config item(s)
  --print K             print required config item(s) and exit

build options:
  --dry-run             list tasks to be executed and exit
  --force, -f           force tasks rebuild
  --skip SKIPPED_TASKS  skip specified task
```

***

## Logging

### Levels
**`nmk`** prints logs on different levels, and stdout log display can be configured using one of the verbosity options:
- **`--info`** (default): only info (**[I]**) and higher level logs will be displayed
- **`-q, --quiet`**: only warning (**[W]**) and error (**[E]**) logs will be displayed
- **`-v, --verbose`**: all logs (including debug (**[D]**) ones) will be displayed

### File
In addition to the displayed ones, logs are persisted in a file, configured with **`--log-file`** option.
Default log file is **`{ROOTDIR}/.nmk/nmk.log`** (**`{ROOTDIR}`** being the root folder -- see below).

The log file is logging all levels (including debug one), whatever is the chosen level for stdout display (see above).
It uses a rotating mechanism, to start a new log file as soon as a given size (1MB) is reached. Up to 5 backup log files are
kept before being deleted. At the moment, log file size + backup count is hard coded and can't be configured.

### Disabling logs
Logs can be completely disabled (both displayed and persisted ones) if the **`--no-logs`** option is used.

(parser-log-prefix)=
### Prefix

*<span style="color:green">Added in version 1.2.0</span>*

Top level tools that call **`nmk`** can add a log prefix thanks to the **`--log-prefix`**, in order to help identifying different runs (e.g. for different nmk projects folders). See `<prefix>` location in logs displays formats below.

### Format
In quiet/info mode, logs are displayed using this format:
> **`<day> <time> (<level>) <prefix> <logger>|[<task>] <emoji> - <string>`**

Example:
```
2022-02-15 18:21:16 (I) nmk ⏬ - Caching remote references...
2022-02-15 18:21:16 (I) nmk 🏁 - Nothing to do
```

In verbose mode, logs are displayed with a bit more details, using this format:
> **`<day> <time>.<ms> (<level>) <prefix> <logger>|[<task>] <emoji> - <string> - <file>:<function>:<line>`**

Example:
```
2022-02-16 08:02:06.641 (D) nmk 🐛 - ----- nmk version 0.0.0.post27+gb055fcc ----- - logs.py:logging_setup:62
2022-02-16 08:02:06.641 (D) nmk 🐛 - called with args: Namespace(config=None, dry_run=False, log_file='{ROOTDIR}/.nmk/nmk.log', log_level=20, nmk_dir=PosixPath('/tmp/dev/nmk/.nmk'), no_cache=True, no_logs=False, print=None, project='github://dynod/nmk/main/src/tests/templates/remote_repo_ref_valid.yml', root=PosixPath('/tmp/dev/nmk'), tasks=[]) - logs.py:logging_setup:63
2022-02-16 08:02:06.642 (D) nmk 🐛 - Cache cleared! - logs.py:logging_setup:65
2022-02-16 08:02:06.642 (D) nmk 🐛 - New static config pythonPath with value '[]' - model.py:add_config:41
2022-02-16 08:02:06.642 (D) nmk 🐛 - New static config BASEDIR with value '' - model.py:add_config:41
2022-02-16 08:02:06.642 (D) nmk 🐛 - New static config ROOTDIR with value '/tmp/dev/nmk' - model.py:add_config:41
2022-02-16 08:02:06.642 (D) nmk 🐛 - New static config CACHEDIR with value '/tmp/dev/nmk/.nmk' - model.py:add_config:41
2022-02-16 08:02:06.642 (D) nmk 🐛 - New static config PROJECTDIR with value '' - model.py:add_config:41
2022-02-16 08:02:06.642 (D) nmk 🐛 - New static config ENV with value '{...}' - model.py:add_config:41
2022-02-16 08:02:06.642 (I) nmk ⏬ - Caching remote references... - cache.py:download_file:30
2022-02-16 08:02:06.644 (D) urllib3.connectionpool Starting new HTTPS connection (1): github.com:443 - connectionpool.py:_new_conn:1001
2022-02-16 08:02:06.857 (D) urllib3.connectionpool https://github.com:443 "GET /dynod/nmk/archive/refs/heads/main.zip HTTP/1.1" 302 123 - connectionpool.py:_make_request:456
2022-02-16 08:02:06.859 (D) urllib3.connectionpool Starting new HTTPS connection (1): codeload.github.com:443 - connectionpool.py:_new_conn:1001
2022-02-16 08:02:07.082 (D) urllib3.connectionpool https://codeload.github.com:443 "GET /dynod/nmk/zip/refs/heads/main HTTP/1.1" 200 None - connectionpool.py:_make_request:456
2022-02-16 08:02:07.128 (D) nmk 🐛 - PROJECTDIR updated to /tmp/dev/nmk/.nmk/cache/b38e130bed1f28a29781827a5548ac2bdb981eaf/nmk-main/src/tests/templates - files.py:__init__:84
2022-02-16 08:02:07.128 (D) nmk 🐛 - Loading model from /tmp/dev/nmk/.nmk/cache/b38e130bed1f28a29781827a5548ac2bdb981eaf/nmk-main/src/tests/templates/remote_repo_ref_valid.yml - files.py:__init__:96
2022-02-16 08:02:07.129 (D) nmk 🐛 - Loading model schema from /tmp/dev/nmk/venv/lib/python3.8/site-packages/nmk/model/model.yml - files.py:load_schema:64
2022-02-16 08:02:07.144 (D) nmk 🐛 - Loading model from /tmp/dev/nmk/.nmk/cache/b38e130bed1f28a29781827a5548ac2bdb981eaf/nmk-main/src/tests/templates/simplest.yml - files.py:__init__:96
2022-02-16 08:02:07.151 (D) nmk 🐛 - 0 built tasks - build.py:build:66
2022-02-16 08:02:07.151 (I) nmk 🏁 - Nothing to do - __main__.py:nmk:32

```

***

## Root folder

### Defining the root folder
The **`nmk`** root folder is by default located as the parent of the currently activated Python virtualenv (i.e. the one containing the currently running version of **`nmk`**). Relatively to this root folder, **`nmk`** will setup a cache folder (called **`.nmk`**) used to store logs, and temporary files to speed up following builds.

This default location for the root folder has been chosen to allow multiple sub-projects to share the same Python virtualenv and cache folders.

The root folder can also be configured to a custom location using the **`-r, --root`** option.

### Clear cache
When using **`--no-cache`** option, the cache folder (see above) is cleared before running the build.

***

## Project

The project file is the main entry point to declare tasks for **`nmk`** build.

It is configured using the **`-p, --project`** option, and can be either a local path, or a remote URL.

Default project file is **`nmk.yml`** (relative to current working directory).

Project file is a [YAML](https://yaml.org/) file, and has to conform with [this format](file).

***

## Config

Configuration is handled through the **`config`** node of project files.

### Extra configuration

In addition to project files content, extra configuration can be provided through the **`--config`** option. This option allows to define additional config items, or override config items from project files. The option value must be either:
- a valid json object
- or a K=V string, allowing to configure a K item with V string value (only string value allowed, other types shall be contributed through JSON format)

```{note}
- The **`--config`** options contributed configuration is applied __after__ the whole project file model has been loaded.
- On Linux (or git-bash), completion is provided for config item names (including only non-final ones)
```

### Print configuration

The **`--print`** option can be used to dump any configuration item value, after the project file model has been loaded (and after the **`--config`** option has been applied, if any). This dump will be displayed as a json object (each **`--print`** option value being a key of the object).

```{note}
- Once the dump is displayed, **`nmk`** will exit (the build phase is completely skipped).
- If **`-q | --quiet`** option is used, only the json object will be displayed (without logging prefix), ready to be processed by any scripting logic (e.g. **`jq`** or others)
- On Linux (or git-bash), completion is provided for config item names
```


***
## Tasks and build

### Tasks

**`nmk`** will build tasks from names provided as positional arguments on the command line. If no task name is provided, the default task will be built instead.

```{note}
On Linux (or git-bash), completion is provided for tasks names on the command line.
```

### Dry run

If the **`--dry-run`** option is used, **`nmk`** will only print the sequence of tasks descriptions that would be triggered in the current configuration and for the provided arguments, without building anything.

### Force

If the **`--force`** option is used, there are no "outputs vs inputs" checks ans all tasks are forced to be rebuilt.

### Skip

If the **`--skip`** option is used, the specified tasks and theirs dependencies are skipped during build.

Example:
> ```shell
> $ nmk --skip prologue  # skips prologue task and all tasks declared as its dependencies
> ```

```{note}
On Linux (or git-bash), completion is provided for tasks names for **`--skip`** option
```
