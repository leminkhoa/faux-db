# CLI Overview

faux-db exposes one command-line entry point:

```bash
faux
```

## Command groups

| Command | Purpose |
| --- | --- |
| `faux init` | Scaffold a starter project structure |
| `faux config validate` | Validate providers, catalogs, and schemas |
| `faux schema generate` | Generate data from a schema file or a domain directory |

There is also a hidden backward-compatible alias:

```bash
faux generate <path>
```

## Typical workflow

```bash
faux init demo-project
faux config validate demo-project
faux schema generate demo-project/schemas/example
```

## CLI pages

- [init](init.md)
- [config validate](config-validate.md)
- [schema generate](schema-generate.md)
