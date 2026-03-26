# Configuration Overview

faux-db configuration is split across a few directories rather than one large
file. That makes each concern easier to reason about and easier to reuse.

## Configuration map

<div class="mermaid">
flowchart LR
    A[schemas/] -->|references| B[providers/]
    A -->|references| C[functions/]
    A -->|declares output| D[outputs/]
    B -->|template_choice uses| E[catalogs/]
    B -->|file_reader uses| F[seeds/]
</div>

## What belongs where

| Area | Put this here |
| --- | --- |
| `schemas/` | Table definitions, column behavior, and output settings |
| `providers/` | Reusable named generators and provider-level options |
| `catalogs/` | YAML vocabularies and reference lists used by templates |
| `seeds/` | CSV source files used by `file_reader` providers |
| `functions/` | Custom Python code called by `func` columns |

## Recommended authoring order

1. create or update providers, catalogs, seeds, or functions
2. reference them from schema files
3. validate with `faux config validate`
4. generate a single schema or a whole domain

## Configuration pages

- [Catalogs](catalogs.md)
- [Providers](providers.md)
- [Schemas](schemas.md)
- [Seeds](seeds.md)
- [Functions](functions.md)
