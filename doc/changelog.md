# Changelog

Here are listed all the meaningfull changes done on **`nmk`** since version 1.0

```{note}
Only interface and important behavior changes are listed here.

The fully detailed changelog is also available on [Github](https://github.com/dynod/nmk/releases)
```

## Release 1.3

### 1.3.0

* Changed default value for **`--log-file`** option (see {ref}`Logs file<parser-log-file>`)

## Release 1.2

### 1.2.0

* New **`--log-prefix`** option (see {ref}`Logs prefix<parser-log-prefix>`)

## Release 1.1

### 1.1.2

* Fix types resolution for config item pure references (see {ref}`Resolved config item type<resolved-config-type>`)

### 1.1.1

* Added capability to escape config item references (see {ref}`Escaped references<refs-escaping>`)

### 1.1.0

* New **`PACKAGESREFS`** {ref}`built-in<builtin-config>` config item, listing all referenced python packages from project files.