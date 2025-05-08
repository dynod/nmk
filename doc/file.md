# Project file format

Project files for **`nmk`** are [YAML](https://yaml.org/) files, and have to conform with the format described on this page.

## Version

Project files don't embed any version at the moment, since there is only one file format version.
Versioning may be introduced in the future if needed.

***

## References

Project files can reference any other project file. This allows to break down the build definition into a very modular layout, by mixing local project tasks with remote "plug-ins" providing reusable tasks.

References are defined as an array value for **`refs`** top-level project property.

### Local references
Any project file can reference any other project file, by simply specifying its path. Following paths are supported:
- relative paths (reckoned relatively to referencing project file parent directory)
- absolute paths (accepted, but will raise a warning during the build)
  ```{warning}
  Using absolute paths is typically non-portable, and should be avoided
  ```

> Example:
> ```yaml
> refs:
>     - someOtherProject.yml
> ```

### URL references
A project file can reference another project file using an URL. Following URLS are supported:
- direct HTTP URL to a YAML project file
  ```{note}
  When using direct URL, if the referenced file uses itself local relative references, these references won't be resolved and build will end with an error
  ```
- HTTP URL to a remote archive, with a sub-path to a YAML project file inside this archive.
This archive will be extracted in the **`nmk`** [cache folder](Basic-usage#cache).
The project sub-path is specified using a **`!<path>`** suffix, identifying the path relatively to the archive root.
Supported archive formats are:
  - zip
  - tar, tar.*, tgz
- **`github://`** URL, which is a shortcut to Github generated ZIP files for branches and tags.
The exact syntax is **`github://<people>/<repo>/<version>/<subpath>`**, which translates to:
  - **`https://github.com/<people>/<repo>/archive/refs/tag/<version>.zip!<repo>-<version>/<sub-path>`** if version starts with a digit (assuming that **`<version>`** is a tag name)
  - **`https://github.com/<people>/<repo>/archive/refs/heads/<version>.zip!<repo>-<version>/<sub-path>`** otherwise (assuming that **`<version>`** is a branch name)
- **`pip://`** URL, allowing to reference a project file bundled in a python package that can be installed with **pip**

> Example:
> ```yaml
> refs:
>     - https://github.com/dynod/nmk/raw/main/src/tests/templates/simplest.yml
>     - https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/src/tests/templates/simplest.yml
>     - github://dynod/nmk/main/src/tests/templates/simplest.yml ## Same as above, but shorter version!
>     - pip://nmk-python!plugin.yml
> ```

### Repository definition
A repository is defined:
- either as a simple string defining the repository remote URL
- or as an object allowing to define more details about the repository, including:
  - its **`remote`** URL (mandatory)
  - its **`local`** path (optional; if expected to be found as cloned locally; typically happens when the referencing project is cloned as a submodule)
  - an **`override`** boolean option (optional, default is False); if set to true, all references (in the whole project) to this repository remote path will be replaced by references to the local path

> Example:
> ```yaml
> refs:
>     - sampleRepo: https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main
>     - workspaceRepo:
>         remote: https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/shared
>         local: ../../shared
> ```

The **`remote`** URL is expected to point at a remote archive (see above for supported URL and archive formats).

If a **`local`** path is specified, **`nmk`** will check if the corresponding path (relative to current project file containing directory) exists:
- if yes, references will be searched in this local path, and the remote archive won't be cached.
- if it doesn't exist, **`nmk`** will simply ignore it and get back to the remote archive extraction behavior.

### Repository relative reference
A repository relative reference is declared by using this syntax: **`<repo name>/path/to/file.yml`**

```{note}
The **`refs`** array order is meaningless regarding repositories definition vs. repository relative references.
```

> Example:
> ```yaml
> refs:
>     - sampleRepo: https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main
>     - <sampleRepo>/src/tests/templates/simplest.yml
>     - <workspaceRepo>/common.yml
>     - workspaceRepo:
>         remote: https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/shared
>         local: ../../shared
> ```

***

## Configuration

Project files can define a set of configuration items, used to tune the build behavior.

Configuration is defined as an object value for **`config`** top-level project property. Values can be any string, integer, boolean, array or object value.

### Overriding items

Any project file can override a config item defined by another referenced project file, with behavior explained in following chapters.

#### Overridden value type

When overriding an item, the value type can't change (e.g. a string item must be overridden by a string value)

> Example of invalid override
>
> file1.yml:
> ```yaml
> config:
>   someItem: my value
> ```
> 
> file2.yml:
> ```yaml
> refs:
>   - file1.yml
> config:
>   someItem: 123 # someItem was initially declared as a string; overriding it as an integer will cause an error
> ```

#### Final items

Items with their name in uppercase (i.e. name only containing [A-Z0-9_] characters) are considered as final, and can't be overridden.

> Example of invalid override
>
> file1.yml:
> ```yaml
> config:
>   MY_CONST1: foo
> ```
> 
> file2.yml:
> ```yaml
> refs:
>   - file1.yml
> config:
>   MY_CONST1: bar # Can't override a final item
> ```

#### Merged values

Depending on value type, some config item values can be merged when overridden:
- when overriding an array, array new values are appended to the old ones (instead of simple replacing them)
- when overriding an object, the new and old objects are merged (i.e. existing keys will be replaced, others will be added)
- when overriding any other type, value is simply replaced

> Example of array/object override
>
> file1.yml:
> ```yaml
> config:
>   someList: [1,2]
>   someDict:
>     abc: 1
>     def: 2
> ```
> 
> file2.yml:
> ```yaml
> refs:
>   - file1.yml
> config:
>   someList: [3,4]
>   someDict:
>     abc: 3
>     ghi: 4
> ```
> 
> Resulting config values:
> ```shell
> $ nmk -p file2.yml --print someList --print someDict -q
> { "someList": [1, 2, 3, 4], "someDict": { "abc": 3, "def": 2, "ghi": 4 } }
> ```

```{note}
**`nmk`** doesn't handle lists of lists. Contributing through references a list in another list will just extend the initial list.
```

> Example of list concatenation
>
> file1.yml:
> ```yaml
> config:
>   someList: [1,2]
> ```
> 
> file2.yml:
> ```yaml
> refs:
>   - file1.yml
> config:
>   someOtherList: [3,4]
>   someList:
>     - ${someOtherList}
> ```
> 
> Resulting config values:
> ```shell
> $ nmk -p file2.yml --print someList -q
> { "someList": [1, 2, 3, 4] }
> ```

### Dynamic config items, using resolvers

Instead of providing a static value, a config item can define a resolver, which is a Python class responsible to dynamically compute the config item value. Specifying a resolver is done by declaring the config item as an object, and set the **`__resolver__`** property.
> Example of resolver definition
> ```yaml
> config:
>   myDynamicItem:
>     __resolver__: mymodule.MyResolver
> ```

Resolvers are always referenced using a fully qualified name (i.e. **`<Python module>.<class name>`**). Referenced class must inherit from the {py:class}`nmk.model.resolver.NmkConfigResolver` class from the **`nmk`** API.

Resolvers can have parameters, provided to the **`get_value`** method as keyword arguments. These parameters are specified through an additional **`params`** property.
> Example of resolver with parameters
> ```yaml
> config:
>   myDynamicItem:
>     __resolver__: mymodule.MyResolverWithParams
>     params:
>       foo: bar
> ```

```{note}
If a resolved item is used to override a static item, the same rule applies as above: the item type can't change (e.g. a static int item can be only overridden by a resolver returning an int value).

The same applies also if a static item overrides a resolved item.
```

### Config item references

When building a string as a value of a config item, other config items can be referenced as variables, using the **`${name}`** syntax. When the value is resolved, the config item name will be replaced by its value.

#### Recursive resolution

If the resolved config value is itself a string referencing another config item, the resolution will be recursive (until everything is resolved).

Example:

> file.yml:
> ```yaml
> config:
>   someString: --${someOtherString}--
>   someOtherString: foo
> ```
> 
> Resulting config value:
> ```shell
> $ nmk -p file.yml --print someString -q
> { "someString": "--foo--" }
> ``

#### Object values

If the resolved config value is an object, it is possible to reference this object keys using a the **`${name.key}`** syntax (and so on if the newly resolved value is itself an object).

Example:

> file.yml:
> ```yaml
> config:
>   someConfig: ${someDict.abc.def}
>   someDict:
>     abc:
>       def: 123
> ```
> 
> Resulting config value:
> ```shell
> $ nmk -p file.yml --print someConfig -q
> { "someConfig": "123" }
> ```

#### Object keys

References can be used as well in object keys.

Example:

> file.yml:
> ```yaml
> config:
>   someConfig: ${someDict.foo}
>   someOtherString: foo
>   someDict:
>     ${someOtherString}: 456
> ```
> 
> Resulting config value:
> ```shell
> $ nmk -p file.yml --print someConfig -q
> { "someConfig": "456" }
> ```

#### Relative paths

Using the **`${r!name}`** syntax will try to convert the referenced value to a path relative to the current project one. Specific behaviors:
  * if the referenced value is a list, all list items will be converted to a relative path
  * if the referenced value is a dict, all dict values will be converted to a relative path
  * if any relative path conversion fails (value is not relative to project path), the build will fail

(refs-escaping)=
#### Escaped references

*<span style="color:green">Added in version 1.1.1</span>*

Sometimes a config item value may contain a string similar the **`nmk`** reference syntax (i.e. **`${SomethingThatIsNotAnNmkConfigItem}`**).
In order to prevent **`nmk`** trying to resolve this as another config item, it is possible to escape this reference by doubling the **`$`** sign.

Example:

> file.yml:
> ```yaml
> config:
>   someConfig: $${SomeUnknownItem}
> ```
> 
> Resulting config value:
> ```shell
> $ nmk -p file.yml --print someConfig -q
> { "someConfig": "${SomeUnknownItem}" }
> ```

(builtin-config)=
### Built-in config items

Following items are built-in and contributed by **`nmk`** itself
Name | Type | Description
---- | ---- | -----------
**`ROOTDIR`** | Path | path to the **`nmk`** root directory (parent of the venv folder)
**`ROOTDIR_NMK`** | Path | path to the **`.nmk`** directory relative to root folder (where will be written nmk log files)
**`CACHEDIR`** | Path | path to the **`nmk`** cache directory
**`PROJECTDIR`** | Path | path to the parent directory of the main project file (the one specified as main **`nmk`** input for the current build)
**`PROJECTDIR_NMK`** | Path | path to the **`.nmk`** directory relative to project folder
**`PROJECTFILES`** | list | list of all resolved project files (by following references from main project file)
**`ENV`** | dict | current **`nmk`** process environment variables
**`BASEDIR`** | str | path to the parent directory of the currently processed project file
**`PACKAGESREFS`** | list | list of all referenced python packages from project files (using **`pip://`** style references)<br> <br>*<span style="color:green">Added in version 1.1</span>*


***

## Tasks

Tasks are the executable elements triggered by **`nmk`** when running the build, ordered by dependencies relationships.

Tasks are defined as an object value for **`tasks`** top-level project property. Keys are the task names, and values are objects holding the different tasks properties.

### Description

The **`description`** property gives a short indication of what the task is doing. It will be displayed by **`nmk`** when the tasks is triggered.

### Emoji

The **`emoji`** property identifies an emoji used to decorate the task logs. It can be either:
- an emoji name (**`nmk`** uses the python [rich](https://github.com/Textualize/rich) library for rendering. See available [emoji codes](https://github.com/Textualize/rich/blob/master/rich/_emoji_codes.py))
- a rich [console markup](https://rich.readthedocs.io/en/latest/markup.html) string (typically allowing to concatenate several emojis)

It will be displayed by **`nmk`** when the tasks is triggered.

### Silent

The **`silent`** property is a boolean flag indicating if task description shall be logged on INFO level (if True; default) or on DEBUG one (if False) when the task is triggered. This is typically convenient for tasks that always need to be triggered, without always updating their output.

### Default

The **`default`** property is a boolean flag indicating if this task shall be considered as the new default task (i.e. the one built when **`nmk`** is launched without explicit tasks to be built). The last declared default task by references order will be the effective default one.

### Inputs and outputs

Any task can declare a set of inputs (**`input`** property) and/or outputs (**`output`** property). These properties can be either:
- a string
- or a list of strings

Configuration items references (using the **`${item}`** syntax) can be used, typically to make these inputs/outputs more customizable by the end user.

Inputs and outputs are referencing paths, and are processed by **`nmk`** when the task is about to be triggered in the dependency chain:
- if the task is missing inputs, outputs, or both, it will be systematically triggered
- otherwise (i.e. the task has both inputs and outputs):
  - all the task inputs __must__ exist (unless explicitly allowed by the builder class **`allow_missing_input`** method)
  - the task will be triggered only if the most recent input has been modified __after__ the oldest output

```{note}
As soon as a given task has inputs, all the project files (i.e. the content of the **`PROJECTFILES`** config item) will be also considered as inputs when computing this update check (assuming that any project file update shall trigger all tasks rebuild)
```

### Dependencies

Dependency relationships between tasks are handled using the following properties:
- the **`deps`** property allow to reference tasks to be considered as dependencies of it
- the **`appendToDeps`** property allow to register this task as an additional dependency of the referenced task (the dependency is added at the end of the current dependencies list)
- the **`prependToDeps`** property allow to register this task as an additional dependency of the referenced task (the dependency is added at the beginning of the current dependencies list)

When **`nmk`** computes the tasks to be built (starting from either the default one, or the command line specified ones), it will resolve the dependencies to make sure that any task is always triggered after all of its dependencies.

### Builder

A given task implementation is delegated to a builder python class, specified through the **`builder`** property. Builders are always referenced using a fully qualified name (i.e. **`<Python module>.<class name>`**). Referenced class must inherit from the {py:class}`nmk.model.builder.NmkTaskBuilder` class from the **`nmk`** API.

The **`build`** method of the builder will be invoked if **`nmk`** decides to trigger the task (see above). This method can take input parameters, specified by the task **`params`** property (which is an object defining these parameters by keywords). These parameters can also reference configuration items (using the **`${item}`** syntax).

```{note}
A task may not define a builder. In that case it will never be "triggered" (nothing to do), and is typically used to group other tasks in its dependencies (being a kind of "meta-task").
```

### Conditions

Task trigger can be conditioned using the value of some configuration items:
* when the task declares a config item reference in its **`if`** property, the task will be triggered only if the config item value is "set"
* when the task declares a config item reference in its **`unless`** property, the task will be triggered unless the config item value is "set"

A config item value is considered as "set" depending on the config value type
| **Type** | **Considered as "set" if** |
| -------- | -------------------------- |
| str      | Non empty, and different from "0" and "false" (case insensitive) |
| int      | != 0 |
| bool     | True |
| list     | Non empty |
| dict     | Non empty |

Any other type will raise an error

### Built-in tasks

**`nmk`** automatically defines following tasks:

* **`prologue`**: meta-task (i.e. without builder), systematically added __before__ all tasks specified on the command line. It can typically be used to hook systematic checks before any task is executed.

* **`epilogue`**: meta-task (i.e. without builder), systematically added __after__ all tasks specified on the command line. It can typically be used to hook systematic checks after all other tasks are executed.

***

## Contributing to python path

For elements referencing a Python class (config items, build tasks), the referenced module is expected to be found on the Python path of the running **`nmk`** instance. If the referenced module is not installed in this instance virtualenv but in a local file, it is possible to dynamically contribute to the Python path by adding value(s) to the top-level **`path`** array item. Contributed values should be relative to the current project file parent directory.

> Example of resolver definition
> ```yaml
> path:
>   - src  ## src sub-folder (relative to this file) contains a mymodule.py file defining the MyResolver class
> config:
>   myDynamicItem:
>     __resolver__: mymodule.MyResolver
> ```
