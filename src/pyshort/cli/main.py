"""Main CLI entry point for PyShorthand tools."""

import argparse
import sys


def main() -> int:
    """Main entry point for pyshort CLI."""
    parser = argparse.ArgumentParser(
        description="PyShorthand Protocol Toolchain",
        epilog="Use 'pyshort <command> --help' for more information on a specific command.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse PyShorthand files")
    parse_parser.add_argument("input", help="Input .pys file")
    parse_parser.add_argument("-o", "--output", help="Output JSON file")
    parse_parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    # Lint command
    lint_parser = subparsers.add_parser("lint", help="Validate and lint PyShorthand files")
    lint_parser.add_argument("input", help="Input .pys file or directory")
    lint_parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    lint_parser.add_argument("--json", action="store_true", help="Output diagnostics as JSON")

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "parse":
        from pyshort.cli.parse import parse_command

        return parse_command(args)
    elif args.command == "lint":
        from pyshort.cli.lint import lint_command

        return lint_command(args)
    elif args.command == "version":
        from pyshort import __version__

        print(f"PyShorthand v{__version__}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
