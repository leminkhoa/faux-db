# faux-db

`faux-db` is a configuration-driven fake data generation toolkit.

## How it works

`faux-db` builds datasets from YAML schemas (tables + columns), generating values using `faker` (via `type: faker`) and custom providers/functions.
Generation is orchestrated by a dependency graph (DAG) so columns and tables are produced in the required order.
Relational data is supported with `type: rel` (aka `$rel`): you can reference values from other generated tables (for example parent-child keys), with `strategy: random|sequential` controlling how related values are distributed.

For full guides, architecture, configuration references, and CLI documentation, visit:

**https://leminkhoa.github.io/faux-db/**

## Install

```bash
pip install faux-db
```

## Quickstart

```bash
faux schema generate schemas/products.yml
```

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
