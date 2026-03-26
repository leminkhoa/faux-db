# Configuration Cheatsheet

Use this page as a quick lookup when writing Kuriboh configuration files.

## Schema skeleton

```yaml
table_name:
  rows: 100
  columns:
    col_a:
      type: faker
      method: word
    col_b:
      type: provider
      target: MyProvider
  output:
    format: csv
    filepath: ./outputs/table_name.csv
```

## Column types

### Faker column

```yaml
email:
  type: faker
  method: email
  unique: true
```

### Provider column

```yaml
segment:
  type: provider
  target: UserSegmentProvider
```

### Relationship column

```yaml
user_id:
  type: rel
  target: users.id
  strategy: sequential
```

### Function column

```yaml
slug:
  type: func
  func: functions.text.make_slug
  params:
    source: '{{ col("title") }}'
```

## Provider types

### `random_choice`

```yaml
UserSegmentProvider:
  type: random_choice
  choices: [new, repeat, vip]
  weights: [0.6, 0.3, 0.1]
```

### `template_choice`

```yaml
WelcomeLineProvider:
  type: template_choice
  templates:
    - '{{ catalog("demo.greetings") | cycle }} {{ catalog("demo.user_suffixes") | random }}'
```

### `expression`

```yaml
ScoreProvider:
  type: expression
  exp: '{{ random_int(1, 100) }}'
```

Only `random_int(min, max)` is supported at the moment.

### `file_reader`

```yaml
CountrySeedProvider:
  type: file_reader
  filepath: countries.csv
  loaded_columns: [country_code, country_name]
```

## Lookup mode

```yaml
country_name:
  type: provider
  target: CountrySeedProvider
  mode: lookup
  lookup:
    key_columns: [country_code]
    key_from: country_code
    value_column: country_name
    on_missing: null
```

## Catalog expression

```jinja
{{ catalog("demo.greetings") | random }}
{{ catalog("demo.user_suffixes") | first }}
{{ catalog("demo.user_suffixes") | default("friend") | cycle }}
```

## Output formats

```yaml
output:
  format: csv
  filepath: ./outputs/users.csv
```

```yaml
output:
  format: json
  filepath: ./outputs/users.json
```
