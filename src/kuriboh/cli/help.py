from __future__ import annotations

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "max_content_width": 100,
}

ROOT_HELP = """Generate sample data and validate Kuriboh projects.

\b
Common patterns:
  kuriboh init
  kuriboh init demo-project
  kuriboh config validate
  kuriboh schema generate schemas/example
  kuriboh schema generate schemas/example/users.yml

Use `kuriboh <command> --help` to see examples and detailed guides for each command group.
"""

INIT_HELP = """Create a starter Kuriboh project structure.

\b
Examples:
  kuriboh init
  kuriboh init demo-project
  kuriboh init demo-project --force

\b
What gets created:
  - schemas/ with a runnable example schema
  - providers/ with sample provider definitions
  - catalogs/ with catalog data used by template providers
  - seeds/, outputs/, and functions/ for project expansion
"""

CONFIG_HELP = """Inspect and validate project configuration.

\b
Examples:
  kuriboh config validate
  kuriboh config validate ./demo-project

\b
Validation includes:
  - provider configuration loading
  - catalog discovery and duplicate-name checks
  - schema parsing and column-level validation
  - domain dependency validation across related schema files
"""

CONFIG_VALIDATE_HELP = """Validate providers, catalogs, and schemas under a project root.

\b
Examples:
  kuriboh config validate
  kuriboh config validate .
  kuriboh config validate ./demo-project
"""

SCHEMA_HELP = """Generate data from schema files or domain directories.

\b
Examples:
  kuriboh schema generate schemas/example
  kuriboh schema generate schemas/example/users.yml

\b
Tip:
  Pass a directory to generate all schema files in dependency order.
"""

SCHEMA_GENERATE_HELP = """Generate data from a schema file or schema directory.

\b
Examples:
  kuriboh schema generate schemas/example
  kuriboh schema generate schemas/example/users.yml
"""
