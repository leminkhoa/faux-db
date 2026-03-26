# faux-db

`faux-db` is a configuration-driven fake data generation library that leverages the power of `faker` to create realistic datasets based on YAML definitions. It's designed with a strong emphasis on separation of concerns, allowing for highly modular and reusable data generation components.


## Features

- Declarative: define your data schemas in simple, human-readable YAML.
- Extensible: create custom data catalogs and provider logic for any domain.
- Separation of Concerns: keep table schemas, generation logic, and custom data neatly organized.
- Relationship Management: generate related rows across tables using `type: rel` (`$rel`) and column references.

## Full Documentation

See: https://leminkhoa.github.io/faux-db/

## Install

```bash
pip install faux-db
```

## Quickstart

```bash
faux init
faux schema generate schemas/products.yml
```

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
