# Generation Flow

This page explains what faux-db does after you run a command such as:

```bash
faux schema generate schemas/example
```

## End-to-end flow

<div class="mermaid">
sequenceDiagram
    participant U as User
    participant C as CLI
    participant P as Parsers
    participant R as Provider Registry
    participant D as DAG Builder
    participant X as Resolvers
    participant S as Sink

    U->>C: faux schema generate &lt;path&gt;
    C->>P: load schema, providers, catalogs
    P->>R: validate and build providers
    P->>D: build table and column dependencies
    D->>X: execution order
    X->>X: resolve each column for each row
    X->>S: write completed rows
    S-->>U: csv/json output created
</div>

## Single-table generation

For one schema file, faux-db:

1. loads and validates the schema
2. loads providers and catalogs
3. builds the provider registry
4. plans column order from dependencies such as `{{ col("...") }}`
5. constructs resolvers for each column
6. generates rows and writes them through the configured sink

## Domain generation

If the path is a directory, faux-db treats it as a domain:

1. every schema file in that directory is loaded
2. table names are checked for uniqueness
3. a table DAG is built from `rel` columns
4. tables are generated in dependency order
5. generated rows are kept in shared context so downstream tables can reference them

## Validation before execution

`faux config validate` runs most of the planning steps without writing output.
That makes it the safest way to verify:

- provider config shape
- duplicate catalog stem errors
- missing column references
- invalid `rel` targets
- domain dependency problems

## Operational advice

- Run validation before generation in CI.
- Generate whole domains when tables depend on each other.
- Keep output paths relative to the project root for portability.
