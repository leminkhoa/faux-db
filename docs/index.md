# Kuriboh Faker

<div class="hero" markdown>
  <p class="hero__eyebrow">Configuration-first synthetic data generation</p>
  <p class="hero__lead">
    Define datasets in YAML, reuse named providers and catalogs, and generate
    CSV or JSON outputs from a single CLI.
  </p>
  <p>
    <a class="md-button md-button--primary" href="getting-started/">Get started</a>
    <a class="md-button" href="architecture/">See how it works</a>
  </p>
</div>

Kuriboh is designed for teams that want fake or sample data without hard-coding
generation logic into ad hoc scripts. You describe tables, columns, and outputs
in YAML; Kuriboh handles validation, ordering, provider lookup, and file writing.

<div class="grid cards" markdown>

- **YAML-first authoring**

  Keep table definitions readable and versionable. A schema file defines rows,
  columns, and output format in one place.

- **Reusable generation building blocks**

  Put shared behavior in `providers/`, lookup data in `catalogs/`, seed files in
  `seeds/`, and custom Python callables in `functions/`.

- **Domain-aware execution**

  Generate one schema file or an entire domain directory. Table dependencies are
  resolved automatically when `rel` columns connect tables together.

- **Built-in validation**

  Validate providers, catalogs, and schemas before generation so broken configs
  fail early.
</div>

## Why teams use it

- Generate realistic development and test data from declarative config.
- Reuse common provider definitions across multiple schemas.
- Keep reference data and templates separate from table structure.
- Produce stable output layouts in `csv` or `json`.

## How it works

1. Create or scaffold a project with `kuriboh init`.
2. Define providers, catalogs, and schemas under the standard project folders.
3. Run `kuriboh config validate` to catch configuration issues early.
4. Generate a single schema or an entire domain with `kuriboh schema generate`.

## Component map

<div class="mermaid">
flowchart LR
    A[schemas/] --> B[Resolvers and DAG planner]
    C[providers/] --> D[Provider registry]
    E[catalogs/] --> D
    F[seeds/] --> D
    G[functions/] --> B
    D --> B
    H[CLI] --> I[Validation or generation]
    I --> B
    B --> J[CSV / JSON sinks]
</div>

## Core concepts

| Concept | What it does |
| --- | --- |
| Schema | Defines one table, its row count, columns, and output path. |
| Provider | A named reusable generator such as `random_choice` or `file_reader`. |
| Catalog | YAML reference data used inside template providers. |
| Domain | A directory of related schema files generated in dependency order. |
| Sink | The output writer selected by `output.format` (`csv` or `json`). |

## Recommended reading order

- Start with [Getting Started](getting-started/index.md) for the setup flow.
- Read [Architecture](architecture/index.md) for the runtime model and generation flow.
- Use [Configuration](configuration/index.md) when authoring schemas, providers, catalogs, and seeds.
- Use [CLI](cli/index.md) when you want command details and operational examples.
