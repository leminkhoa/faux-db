# Project Layout

Kuriboh follows a convention-based layout so commands can infer the project root
and discover config files without extra flags.

## Standard layout

```text
demo-project/
├── catalogs/
├── functions/
├── outputs/
├── providers/
├── schemas/
└── seeds/
```

## Directory reference

| Path | Purpose |
| --- | --- |
| `catalogs/` | YAML reference data for template providers |
| `functions/` | Custom Python callables for `func` columns |
| `outputs/` | Generated CSV and JSON files |
| `providers/` | Reusable named provider definitions |
| `schemas/` | Table schema files grouped by domain |
| `seeds/` | CSV files for `file_reader` providers |

## Discovery behavior

- provider files are loaded from the top level of `providers/`
- catalog files are discovered recursively under `catalogs/`
- schema files are discovered under `schemas/`
- domain directories are usually immediate subdirectories of `schemas/`
