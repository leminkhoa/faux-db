# CLI Overview

Kuriboh exposes one command-line entry point:

```bash
kuriboh
```

## Command groups

| Command | Purpose |
| --- | --- |
| `kuriboh init` | Scaffold a starter project structure |
| `kuriboh config validate` | Validate providers, catalogs, and schemas |
| `kuriboh schema generate` | Generate data from a schema file or a domain directory |

There is also a hidden backward-compatible alias:

```bash
kuriboh generate <path>
```

## Typical workflow

```bash
kuriboh init demo-project
kuriboh config validate demo-project
kuriboh schema generate demo-project/schemas/example
```

## CLI pages

- [init](init.md)
- [config validate](config-validate.md)
- [schema generate](schema-generate.md)
