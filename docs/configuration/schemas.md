# Schemas

Schemas define tables. Each schema file currently contains exactly one top-level
table name with `rows`, `columns`, and `output`.

## Minimal example

```yaml
users:
  rows: 10
  columns:
    id:
      type: faker
      method: uuid4
      unique: true
    email:
      type: faker
      method: email
      bind_to: id
    segment:
      type: provider
      target: UserSegmentProvider
  output:
    format: csv
    filepath: ./outputs/users.csv
```

## Top-level fields

| Field | Required | Meaning | Why it matters |
| --- | --- | --- | --- |
| `rows` | Yes | Number of rows to generate | Controls output size |
| `columns` | Yes | Mapping of output column names to column configs | Defines the dataset shape |
| `output.format` | Yes | Sink type: `csv` or `json` | Controls file format |
| `output.filepath` | Yes | Output path relative to project root | Controls where results are written |

## Column types

### `faker`

Calls a Faker method by name.

```yaml
full_name:
  type: faker
  method: name
```

Common options:

| Option | Meaning | Typical use case |
| --- | --- | --- |
| `method` | Faker method name | `email`, `uuid4`, `name`, `date_time` |
| `params` | Keyword arguments for that method | Methods needing bounds or flags |
| `unique` | Require unique values when possible | IDs, keys, usernames |
| `bind_to` | Reuse cached values for rows sharing the same bound key | Stable derived attributes per entity |

### `provider`

Calls a named provider from the provider registry.

```yaml
segment:
  type: provider
  target: UserSegmentProvider
```

Common options:

| Option | Meaning | Typical use case |
| --- | --- | --- |
| `target` | Provider name defined in `providers/` | Reusable generation logic |
| `mode` | `sample` or `lookup` | `file_reader` workflows |
| `sample` | Sampling settings for `file_reader` providers | Sequential, random, or shuffled sampling |
| `lookup` | Lookup config for `file_reader` providers | Code-to-label or key-to-value mapping |
| `unique` | Ask the resolver for unique output when supported | Controlled distinct samples |
| `bind_to` | Cache generated values per row key | Stable reusable values |

### `rel`

Reads a value from another generated table in the same domain.

```yaml
user_id:
  type: rel
  target: users.id
  strategy: random
```

Options:

| Option | Meaning | Typical use case |
| --- | --- | --- |
| `target` | `<table>.<column>` reference | Parent-child relationships |
| `strategy` | `random` or `sequential` | Distribution control across referenced rows |

### `func`

Calls a Python callable from `functions/`.

```yaml
slug:
  type: func
  func: functions.text.make_slug
  params:
    source: '{{ col("title") }}'
```

Options:

| Option | Meaning | Typical use case |
| --- | --- | --- |
| `func` | Import path to a callable | Custom logic not well expressed in YAML |
| `params` | Keyword arguments passed to the callable | Parameterized transformation |
| `unique` | Unique output when the resolver can support it | Generated slugs or synthetic keys |
| `bind_to` | Cache values by another column | Stable per-entity outputs |

If the callable accepts `context` or `row`, Kuriboh injects them automatically.

## Column references

`func` params can reference previously generated columns:

```yaml
params:
  email: '{{ col("email") }}'
```

These references are validated before generation.

## `file_reader` column helpers

When a provider column uses a `file_reader` provider, two helper blocks matter.

### `sample`

```yaml
sku:
  type: provider
  target: ProductSeedProvider
  mode: sample
  sample:
    strategy: shuffle
    seed: 7
```

| Field | Meaning |
| --- | --- |
| `strategy` | `sequential`, `random`, or `shuffle` |
| `seed` | Optional RNG seed for random or shuffle behavior |

### `lookup`

```yaml
country_name:
  type: provider
  target: CountrySeedProvider
  mode: lookup
  lookup:
    key_columns: [country_code]
    key_from: country_code
    value_column: country_name
    on_missing: default
    default_value: Unknown
```

| Field | Meaning |
| --- | --- |
| `key_columns` | Seed columns used as lookup keys |
| `key_from` | Source column or columns from the current row |
| `value_column` | Seed column to return |
| `on_missing` | `null`, `error`, or `default` |
| `default_value` | Fallback used when `on_missing: default` |

## Best practices

- Keep one table per file.
- Use providers for shared logic and `func` for truly custom behavior.
- Keep output paths under `outputs/` unless you have a strong reason not to.
- Use domain directories when tables reference each other via `rel`.
