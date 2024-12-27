# Install

**`nmk`** can be used without being "installed" (meaning a system-level install).

There are two cases:
* either you want to build an existing **`nmk`** project
* or you want to bootstrap a new one

## Building an existing project

Each **`nmk`** project provides **`buildenv`** loading scripts, that can be "sourced" to bootstrap everything:
* create and load a python venv
* install **`nmk`** (and potentially other project requirements)
* setup **`nmk`** completion

In other words, you can build a freshly cloned nmk project with these two commands:
```shell
$ ./buildenv.sh
$ nmk
```

**_Note for Windows users_**

If you plan to develop your project on Windows, you've probably installed **`git`**. The commands above can then be executed in **`git-bash`** terminal to create the venv.

Or, if you prefer to get back to a Windows **`cmd`** shell, you can load the build environment with this command:
```shell
> buildenv.cmd
> nmk
```

## Bootstrap a new project

If you want to create a new **`nmk`** project, you can simply bootstrap the build environment by following [these instructions](https://buildenv.readthedocs.io/en/stable/usage.html).

You'll then have to create an nmk [project file](file).
**`nmk`** project comes with following examples you can clone or simply get inspiration from:
* [sample python project](https://github.com/dynod/nmk-python-sample)
* [sample rust project](https://github.com/dynod/nmk-rust-sample)
