# `kuriboh schema generate`

Generate data from a schema file or a domain directory.

## Syntax

```bash
kuriboh schema generate <path>
```

## Examples

```bash
kuriboh schema generate schemas/example/users.yml
kuriboh schema generate schemas/example
```

## File vs directory behavior

| Input | Result |
| --- | --- |
| Schema file | Generate one table |
| Directory | Generate every schema file in that directory in dependency order |

## When to pass a directory

Pass a domain directory when:

- tables reference each other with `rel`
- you want shared context across related tables
- you want one command to build a full synthetic dataset slice

## Output behavior

- output format comes from each schema file
- relative paths are resolved from the project root
- supported sinks are `csv` and `json`

## Related command

Use [`kuriboh config validate`](config-validate.md) before generation when you
want to catch configuration issues first.
