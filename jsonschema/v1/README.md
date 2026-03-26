## Kuriboh Faker JSON Schemas (v1)

This folder contains JSON Schema files that provide IDE autocomplete and validation for Kuriboh YAML configuration files.

### What this covers

- **Schemas** (`schemas/**/*.yml|yaml`): table config (`rows`, `columns`, `output`, column `type` etc.)
- **Providers** (`providers/**/*.yml|yaml`): provider registry config (loose schema; provider-specific keys vary by provider type)
- **Catalogs** (`catalogs/**/*.yml|yaml`): catalog YAML files (loose schema; user-defined structure)

### VS Code / Cursor setup

Install the "YAML" extension (Red Hat), then add a workspace mapping in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "./jsonschema/v1/schema-file.schema.json": [
      "schemas/**/*.yml",
      "schemas/**/*.yaml",
      "tests/**/fixtures/schemas/**/*.yml",
      "tests/**/fixtures/schemas/**/*.yaml"
    ],
    "./jsonschema/v1/providers.schema.json": [
      "providers/**/*.yml",
      "providers/**/*.yaml",
      "tests/**/fixtures/providers/**/*.yml",
      "tests/**/fixtures/providers/**/*.yaml"
    ],
    "./jsonschema/v1/catalog.schema.json": [
      "catalogs/**/*.yml",
      "catalogs/**/*.yaml",
      "tests/**/fixtures/catalogs/**/*.yml",
      "tests/**/fixtures/catalogs/**/*.yaml"
    ]
  }
}
```

Notes:
- These schemas validate **structure**, but cannot fully validate cross-file or cross-field semantics (e.g. `$rel` target table existence, `key_from` referencing a real column). The Kuriboh runtime validator still handles those.

