# faux-db

faux-db is a configuration-driven data generation library that leverages the power of `faker` to create realistic datasets based on YAML definitions. It's designed with a strong emphasis on separation of concerns, allowing for highly modular and reusable data generation components.

## Features

-   **Declarative:** Define your data schemas in simple, human-readable YAML.
-   **Extensible:** Create custom data catalogs and provider logic for any domain.
-   **Separation of Concerns:** Keep your table schemas, generation logic, and custom data neatly organized.
-   **Relationship Management:** (Future Goal) Define and generate data with relationships between different tables.

## Project Structure

The project is organized into several key directories:

-   `catalogs/`, `providers/`, `schemas/`, `seeds/`: These directories contain the user-defined YAML configurations and data files.
    -   **Catalogs:** All `*.yml` and `*.yaml` files under `catalogs/` are loaded **recursively** (subfolders allowed). Each file is registered under the **basename** of the file (e.g. `catalogs/common/materials.yaml` → key `materials` for `catalog("materials.material")`). Two files with the same basename in different subfolders raise an error to keep lookups unambiguous.
-   `src/faux/`: Contains the core Python source code for the library, which is broken down into:
    -   `cli.py`: Entrypoint for the command-line interface.
    -   `core/`: The brain of the system, containing the main generation `engine`, `dag` for dependency resolution, and `context` for state management.
    -   `parsers/`: Handles loading and validating all the user's YAML configuration files.
    -   `resolvers/`: Contains the logic for processing different types of data generation nodes (e.g., `$faker`, `$ref`, `$expression`).
    -   `providers/`: Manages the registration and execution of custom data providers.
    -   `sinks/`: Handles writing the generated data to different output formats (CSV, JSON, SQL, etc.).

## Installation

```bash
pip install faux-db
```

## Usage

This library is designed to be used as a command-line tool.

```bash
# Run the data generator
faux schema generate schemas/products.yml
```

This will use the logic defined in the `src/faux` package to:
1.  Parse the `schemas/products.yml` file.
2.  Resolve the dependencies between tables.
3.  Generate the data column by column using the specified resolvers.
4.  (Future) Output the data to a specified sink.

## Configuration Example

### `catalogs/furniture.yml`

```yaml
items:
  - "Sofa"
  - "Chair"
  - "Table"
  - "Bed"
  - "Bookshelf"
```

### `providers/ecommerce.yml`

```yaml
product_name:
  provider: "faker.word" # Uses the 'word' method from the faker library
  # Or a more complex example referencing a catalog
  # furniture_name:
  #   provider: "$catalog.furniture.items"

product_price:
  provider: "faker.pydecimal"
  params:
    left_digits: 3
    right_digits: 2
    positive: true
```

### `schemas/products.yml`

```yaml
products:
  - name: "product_name"
    provider: "ecommerce.product_name"
  - name: "price"
    provider: "ecommerce.product_price"
  - name: "company"
    provider: "seeds.real_companies.name" # Example of using a seed file
```

## Reproducible provider output (testing)

For `random_choice`, `template_choice`, and `expression` providers you can set an optional **`seed`** (integer) in the provider YAML. That provider then uses its own `random.Random` or a dedicated `Faker` with `seed_instance(seed)` so repeated runs with the same config and seed produce the same sequence from that provider. (`Faker.seed()` is global and would affect every generator; we do not call it per provider.) Other columns may still use the global `Faker` / `random` unless they are also seeded.

```yaml
MyPicker:
  type: random_choice
  choices: [a, b, c]
  seed: 42

MyTemplate:
  type: template_choice
  seed: 42
  templates:
    - '{{ catalog("furniture.material") }}'

MyExpr:
  type: expression
  seed: 42
  exp: "{{ faker.random_int(10, 500) }}"
```

**Note:** Unique-column pooling (`enumerate_all` + shuffle) is still driven by the global `random` module in the resolver layer; for fully deterministic CSV output including unique pools, you may also need to seed Python’s global RNG at process start (e.g. `random.seed(...)` before running generation).

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.
