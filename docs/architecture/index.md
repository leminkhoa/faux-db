# System Overview

faux-db is a configuration-driven data generation engine. The project structure
is intentionally split so each concern has one home:

- `schemas/` describes tables and columns
- `providers/` defines reusable named generators
- `catalogs/` stores YAML lookup content for template-based providers
- `seeds/` stores CSV-backed tabular data
- `functions/` stores custom Python callables
- `outputs/` receives generated files

## How the pieces connect

<div class="mermaid">
flowchart TD
    CLI[CLI commands] --> VALIDATE[Validation pipeline]
    CLI --> GENERATE[Generation pipeline]

    CONFIG[schemas/] --> VALIDATE
    PROVIDERS[providers/] --> VALIDATE
    CATALOGS[catalogs/] --> VALIDATE

    PROVIDERS --> REGISTRY[Provider registry]
    CATALOGS --> CONTEXT[Generation context]
    SEEDS[seeds/] --> REGISTRY
    FUNCTIONS[functions/] --> RESOLVERS[Resolvers]
    CONFIG --> DAG[DAG planners]

    VALIDATE --> DAG
    GENERATE --> DAG
    REGISTRY --> RESOLVERS
    DAG --> RESOLVERS
    CONTEXT --> RESOLVERS
    RESOLVERS --> SINKS[CSV / JSON sinks]
    SINKS --> OUTPUTS[outputs/]
</div>

## Runtime responsibilities

| Component | Responsibility |
| --- | --- |
| CLI | Entry point for initialization, validation, and generation. |
| Parsers | Load YAML files and validate them into typed config models. |
| Provider registry | Instantiates named providers from `providers/`. |
| DAG planners | Order columns and tables based on dependencies. |
| Resolvers | Produce individual column values for each row. |
| Generation context | Shares Faker, catalogs, caches, and generated table rows. |
| Sinks | Persist final rows to `csv` or `json`. |

## Why this split matters

- Schema authors can work in YAML without editing Python.
- Reusable providers reduce duplication across many schemas.
- Catalogs and seeds keep reference data outside generation logic.
- Validation catches most mistakes before any files are written.
- Domain execution makes multi-table datasets manageable.

## Next step

Continue with [Generation Flow](generation-flow.md) to see what happens during a
single run from CLI command to output file.
