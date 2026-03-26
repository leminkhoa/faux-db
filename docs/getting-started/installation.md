# Installation

faux-db requires Python `3.11+`.

## Install the library

Assuming `faux-db` is published on PyPI, install it into a virtual
environment:

=== "uv"

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install faux-db
    ```

=== "pip"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install faux-db
    ```

## Verify the installation

```bash
faux --version
faux --help
```

## What gets installed

- the `faux` CLI
- the Python package used to validate and generate data
- support for project scaffolding, validation, and generation workflows

## Next step

Continue with the [Quickstart](quickstart.md) to scaffold a sample project and
generate your first output file.
