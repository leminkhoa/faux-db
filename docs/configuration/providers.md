# Providers

Providers are named reusable generators. A schema column can reference a
provider by name instead of repeating generation logic inline.

## Where they live

Provider files live under `providers/`:

```text
providers/
├── example.yml
└── ecommerce.yml
```

Kuriboh loads all top-level YAML files, validates each provider config, and
merges them into one registry.

## Why use providers

Use providers when:

- multiple schema files need the same generation behavior
- you want business-friendly names like `UserSegmentProvider`
- the logic is more reusable than a one-off `faker` column

## Provider types

### `random_choice`

Returns one item from a fixed list.

```yaml
UserSegmentProvider:
  type: random_choice
  choices: [new, repeat, vip]
  weights: [0.6, 0.3, 0.1]
  seed: 11
```

Options:

| Option | Required | Meaning | When to use it |
| --- | --- | --- | --- |
| `choices` | Yes | Candidate values to sample from | Always |
| `weights` | No | Relative probability for each choice | Biased distributions |
| `seed` | No | Dedicated RNG seed for reproducible provider output | Stable test fixtures |

### `template_choice`

Picks a template string, then resolves catalog placeholders such as
`{{ catalog("demo.greetings") | cycle }}`.

```yaml
WelcomeLineProvider:
  type: template_choice
  seed: 17
  templates:
    - '{{ catalog("demo.greetings") | cycle }} {{ catalog("demo.user_suffixes") | random }}'
    - 'Hello {{ catalog("demo.user_suffixes") | first }}'
```

Options:

| Option | Required | Meaning | When to use it |
| --- | --- | --- | --- |
| `templates` | Yes | Candidate text templates | Generated labels, messages, descriptions |
| `seed` | No | Controls template selection and `| random` slot selection | Deterministic outputs |

Best fit:

- natural-language labels
- composable phrases built from catalogs
- light text generation without custom Python

### `expression`

Evaluates a very small built-in expression language.

```yaml
OrderScoreProvider:
  type: expression
  exp: '{{ random_int(10, 500) }}'
  seed: 42
```

Important:

- this is **not** arbitrary Python
- this is **not** arbitrary Faker access
- it is an allowlisted Kuriboh expression syntax

At the moment, the code only supports one expression name:

- `random_int(min, max)`

That expression is routed to Faker internally, but users should think of it as a
Kuriboh-supported built-in. Integer arguments only are supported right now.

Options:

| Option | Required | Meaning | When to use it |
| --- | --- | --- | --- |
| `exp` | Yes | Expression string in `{{ name(args) }}` form | Compact numeric generation |
| `seed` | No | Creates an isolated seeded Faker instance for this provider | Reproducible score-like fields |

Good use cases:

- simple bounded numeric values
- deterministic score or ranking fields
- small expression-based placeholders without adding a custom function

Use a `func` column instead if:

- you need anything beyond `random_int`
- you need strings, branching, or richer business logic
- you want to call multiple helpers

### `file_reader`

Loads one or more columns from a CSV file in `seeds/`.

```yaml
CountrySeedProvider:
  type: file_reader
  filepath: countries.csv
  loaded_columns: [country_code, country_name]
  delimiter: ","
  encoding: utf-8
  on_duplicate_key: first
```

Options:

| Option | Required | Meaning | When to use it |
| --- | --- | --- | --- |
| `filepath` | Yes | CSV filename under `seeds/` | Always |
| `loaded_columns` | Yes | Columns to load from the CSV | Restrict memory and valid lookup targets |
| `delimiter` | No | CSV separator, default `,` | Non-standard CSV files |
| `encoding` | No | File encoding, default `utf-8` | Legacy exports |
| `on_duplicate_key` | No | Duplicate-key behavior for lookup mode: `first`, `last`, `error` | Lookup-oriented seed data |

Best fit:

- reference datasets already maintained as CSV
- lookup tables such as country codes, SKUs, or ID mappings
- repeatable sampling from controlled tabular data

## Choosing the right provider

| Need | Best choice |
| --- | --- |
| Pick from a known set of values | `random_choice` |
| Assemble strings from catalog content | `template_choice` |
| Generate a simple bounded integer | `expression` |
| Sample or look up values from CSV data | `file_reader` |
