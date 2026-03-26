# Quickstart

This walkthrough uses the built-in starter template created by `faux init`.

## 1. Scaffold a project

```bash
faux init demo-project
```

This creates a minimal working layout with:

- `schemas/example/users.yml`
- `providers/example.yml`
- `catalogs/demo.yml`
- `functions/__init__.py`

## 2. Validate the project

```bash
faux config validate demo-project
```

Validation checks provider configuration, catalog loading, schema parsing, and
domain dependency rules before any data is generated.

## 3. Generate the example domain

```bash
faux schema generate demo-project/schemas/example
```

Because the argument is a directory, faux-db generates every schema file in that
domain in dependency order.

## 4. Inspect the output

The starter schema writes to:

```text
demo-project/outputs/users.csv
```

The example schema looks like this:

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
    welcome_line:
      type: provider
      target: WelcomeLineProvider
  output:
    format: csv
    filepath: ./outputs/users.csv
```

## 5. Customize it

Common next edits:

- Change `rows` to control dataset size.
- Swap a column from `faker` to `provider` for reusable logic.
- Add a `func` column that calls code from `functions/`.
- Change `output.format` to `json`.

## Next step

Read [Schemas](../configuration/schemas.md) to learn the full YAML shape and
supported column options.
