# `faux init`

Create a starter faux-db project structure.

## Syntax

```bash
faux init [path] [--force]
```

## Examples

```bash
faux init
faux init demo-project
faux init demo-project --force
```

## What it creates

- `schemas/`
- `providers/`
- `catalogs/`
- `seeds/`
- `outputs/`
- `functions/`

It also writes starter files such as:

- `schemas/example/users.yml`
- `providers/example.yml`
- `catalogs/demo.yml`
- `functions/__init__.py`

## Option reference

| Option | Meaning |
| --- | --- |
| `path` | Target directory, defaults to the current directory |
| `--force` | Overwrite starter files if they already exist |

## When to use it

- starting a new faux-db project
- creating an example project for a teammate
- refreshing starter files in a controlled way with `--force`
