# `kuriboh init`

Create a starter Kuriboh project structure.

## Syntax

```bash
kuriboh init [path] [--force]
```

## Examples

```bash
kuriboh init
kuriboh init demo-project
kuriboh init demo-project --force
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

- starting a new Kuriboh project
- creating an example project for a teammate
- refreshing starter files in a controlled way with `--force`
