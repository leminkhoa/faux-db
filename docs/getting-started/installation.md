# Installation

Kuriboh requires Python `3.11+`.

## Install the library

Assuming `kuriboh-faker` is published on PyPI, install it into a virtual
environment:

=== "uv"

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install kuriboh-faker
    ```

=== "pip"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install kuriboh-faker
    ```

## Verify the installation

```bash
kuriboh --version
kuriboh --help
```

## What gets installed

- the `kuriboh` CLI
- the Python package used to validate and generate data
- support for project scaffolding, validation, and generation workflows

## Next step

Continue with the [Quickstart](quickstart.md) to scaffold a sample project and
generate your first output file.
