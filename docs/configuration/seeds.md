# Seeds

Seeds are CSV files stored under `seeds/`. They are consumed by `file_reader`
providers.

## When to use seeds

Choose seeds when your source data is naturally tabular, such as:

- country code mappings
- product or SKU reference lists
- organization hierarchies exported from a spreadsheet
- lookup tables maintained outside the codebase

Use catalogs instead when your data is small YAML content intended for
template-based string rendering.

## Example seed file

```csv
country_code,country_name,region
US,United States,North America
FR,France,Europe
JP,Japan,Asia
```

## Connect a seed to a provider

```yaml
CountrySeedProvider:
  type: file_reader
  filepath: countries.csv
  loaded_columns: [country_code, country_name, region]
  delimiter: ","
  encoding: utf-8
  on_duplicate_key: first
```

## Two common usage patterns

### Sampling

Return values from one loaded column, one row at a time.

```yaml
country_code:
  type: provider
  target: CountrySeedProvider
  mode: sample
  column: country_code
  sample:
    strategy: sequential
```

Best for:

- rotating through a seed list
- random or shuffled value assignment
- generating a single column from a curated dataset

### Lookup

Use existing row values as keys and fetch another seed column.

```yaml
country_name:
  type: provider
  target: CountrySeedProvider
  mode: lookup
  lookup:
    key_columns: [country_code]
    key_from: country_code
    value_column: country_name
    on_missing: error
```

Best for:

- code-to-name enrichment
- resolving labels from IDs
- keeping related columns consistent

## Duplicate-key behavior

`on_duplicate_key` controls what happens when multiple seed rows share the same
lookup key:

| Value | Meaning | Use case |
| --- | --- | --- |
| `first` | Keep the first matching row | Stable first-win behavior |
| `last` | Keep the last matching row | Override-style seed files |
| `error` | Fail validation/execution | Strict data quality requirements |

## Best practices

- Keep seed files small and focused by domain.
- Load only the columns you need with `loaded_columns`.
- Use lookup mode when one generated column depends on another.
- Prefer `error` for critical lookup tables where duplicates should never exist.
