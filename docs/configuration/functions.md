# Functions

Functions let you move custom generation logic into Python when YAML becomes too
limited.

## Where they live

Put modules under `functions/` in your faux-db project.

```text
functions/
├── __init__.py
└── text.py
```

## How schemas reference functions

Use a `func` column with an import path:

```yaml
slug:
  type: func
  func: functions.text.make_slug
  params:
    source: '{{ col("title") }}'
```

## Callable behavior

faux-db imports the callable once when planning generation. At runtime it passes:

- declared `params`
- `context` if the function signature accepts `context`
- `row` if the function signature accepts `row`

## Example

```python
def make_slug(source: str) -> str:
    return source.lower().replace(" ", "-")
```

## When to use functions instead of providers

Use functions when:

- logic is too specific for a reusable provider
- you need branching or more complex transformations
- you need direct access to the current row or generation context

Use providers when:

- the logic should be named and reused across many schemas
- the config should stay fully declarative

## Best practices

- Keep functions small and deterministic where possible.
- Prefer explicit parameter names over reading unrelated global state.
- Use functions to complement configuration, not replace it entirely.
