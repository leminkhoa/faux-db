from __future__ import annotations

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "max_content_width": 100,
}

ROOT_HELP = """Generate sample data and validate faux-db projects.

\b
Common patterns:
  faux init
  faux init demo-project
  faux config validate
  faux schema generate schemas/example
  faux schema generate schemas/example/users.yml

Use `faux <command> --help` to see examples and detailed guides for each command group.
"""

INIT_HELP = """Create a starter faux-db project structure.

\b
Examples:
  faux init
  faux init demo-project
  faux init demo-project --force

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
  faux config validate
  faux config validate ./demo-project

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
  faux config validate
  faux config validate .
  faux config validate ./demo-project
"""

SCHEMA_HELP = """Generate data from schema files or domain directories.

\b
Examples:
  faux schema generate schemas/example
  faux schema generate schemas/example/users.yml

\b
Tip:
  Pass a directory to generate all schema files in dependency order.
"""

SCHEMA_GENERATE_HELP = """Generate data from a schema file or schema directory.

\b
Examples:
  faux schema generate schemas/example
  faux schema generate schemas/example/users.yml
"""
