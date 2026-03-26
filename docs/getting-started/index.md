# Getting Started

Kuriboh projects follow a small set of conventions so the CLI can discover
providers, catalogs, schemas, custom functions, and output files without extra
configuration.

## Typical workflow

1. Install the package and confirm the `kuriboh` CLI is available.
2. Run `kuriboh init` to scaffold a starter project.
3. Edit files in `schemas/`, `providers/`, and `catalogs/`.
4. Validate everything with `kuriboh config validate`.
5. Generate one schema file or a full domain directory.

## What `kuriboh init` creates

The starter structure includes:

- `schemas/` for table definitions
- `providers/` for named provider configurations
- `catalogs/` for YAML lookup data used by templates
- `functions/` for custom Python callables
- `seeds/` for CSV-backed providers
- `outputs/` for generated files

## Choose your path

- Read [Installation](installation.md) to set up the environment.
- Follow [Quickstart](quickstart.md) to generate the example dataset in minutes.
- Read [Architecture](../architecture/index.md) to understand how the pieces connect.
- Use [Configuration](../configuration/index.md) when you start authoring real projects.
