# `kuriboh config validate`

Validate a Kuriboh project without generating output files.

## Syntax

```bash
kuriboh config validate [path]
```

## Examples

```bash
kuriboh config validate
kuriboh config validate .
kuriboh config validate ./demo-project
```

## What it checks

- provider file loading and config validation
- catalog discovery and duplicate stem detection
- schema parsing
- column-level validation
- domain dependency ordering
- dry planning for each schema

## Why it matters

This command is the safest way to catch configuration issues before generation.
It is a good fit for:

- local authoring loops
- CI checks on pull requests
- debugging broken schema references

## Option reference

| Option | Meaning |
| --- | --- |
| `path` | Project root, defaults to the current directory |
