import argparse
from pathlib import Path

from .core.engine import run_generation


def main() -> None:
    """
    Usage:

    python main.py generate schemas/products.yml
    """
    parser = argparse.ArgumentParser(prog="kuriboh")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate data from a schema YAML file")
    generate_parser.add_argument(
        "schema_path",
        type=str,
        help="Path to a schema YAML file, e.g. schemas/products.yml",
    )

    args = parser.parse_args()

    if args.command == "generate":
        run_generation(Path(args.schema_path))
