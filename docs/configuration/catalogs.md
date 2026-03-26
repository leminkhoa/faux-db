# Catalogs

Catalogs are YAML files that hold reusable reference values. They are primarily
used by the `template_choice` provider.

## Where they live

Put catalog files anywhere under `catalogs/`.

```text
catalogs/
├── demo.yml
└── shared/
    └── industries.yml
```

faux-db discovers catalog files recursively.

## How files are registered

Each file is registered by its filename stem:

- `catalogs/demo.yml` becomes `demo`
- `catalogs/shared/industries.yml` becomes `industries`

Two files with the same stem are not allowed, even in different folders.

## Example catalog

```yaml
greetings:
  - Welcome aboard
  - Thanks for joining

user_suffixes:
  - explorer
  - builder
  - creator
```

If this file is named `demo.yml`, you can reference it like this:

```jinja
{{ catalog("demo.greetings") }}
{{ catalog("demo.user_suffixes") | random }}
```

## Supported template filters

Catalog access in template providers supports:

| Filter | Meaning | Typical use case |
| --- | --- | --- |
| `random` | Pick a random item from the resolved list | Natural variation in generated text |
| `first` | Always use the first item | Stable deterministic labels |
| `cycle` | Walk through values in order across rows | Even coverage of a small list |
| `default("x")` | Use fallback text if the list is empty | Optional catalogs or sparse data |

If no pick filter is supplied, the default behavior is `random`.

## Best practices

- Keep catalogs small and human-readable.
- Use catalogs for vocabularies, phrases, or business labels.
- Use `seeds/` instead of catalogs for tabular CSV data.
- Give files globally unique names to avoid duplicate stem errors.
