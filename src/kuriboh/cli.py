import argparse
from pathlib import Path

from .core.engine import run_domain, run_generation


def main() -> None:
    """
    Usage:

    python main.py generate schemas/ecommerce
    python main.py generate schemas/ecommerce/products.yml
    """
    parser = argparse.ArgumentParser(prog="kuriboh")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate data from a schema file or domain directory")
    generate_parser.add_argument(
        "domain",
        type=str,
        help="Path to a schema YAML file or a domain directory (e.g. schemas/ecommerce)",
    )

    args = parser.parse_args()

    if args.command == "generate":
        path = Path(args.domain)
        if path.is_file():
            run_generation(path)
        elif path.is_dir():
            run_domain(path)
        else:
            raise FileNotFoundError(f"Not a file or directory: {path}")
