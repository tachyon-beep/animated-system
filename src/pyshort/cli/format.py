"""Format command for PyShorthand CLI."""

import sys
from argparse import Namespace
from pathlib import Path

from pyshort.formatter import FormatConfig, format_file


def format_command(args: Namespace) -> int:
    """Execute the format command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        input_path = Path(args.input)

        # Collect files to format
        files_to_format = []
        if input_path.is_file():
            files_to_format.append(input_path)
        elif input_path.is_dir():
            files_to_format.extend(input_path.rglob("*.pys"))
        else:
            print(f"Error: {args.input} is not a file or directory", file=sys.stderr)
            return 1

        if not files_to_format:
            print(f"No .pys files found in {args.input}", file=sys.stderr)
            return 1

        # Create config
        config = FormatConfig(
            indent=args.indent,
            align_types=not args.no_align,
            prefer_unicode=not args.ascii,
            sort_state_by=args.sort_state,
            max_line_length=args.line_length,
        )

        # Format each file
        for file_path in files_to_format:
            try:
                if args.check:
                    # Check mode: see if file needs formatting
                    with open(file_path, "r", encoding="utf-8") as f:
                        original = f.read()
                    formatted = format_file(str(file_path), config, in_place=False)

                    if original != formatted:
                        print(f"Would reformat: {file_path}")
                        if args.diff:
                            # Show diff (simple version)
                            print(f"\n--- {file_path} (original)")
                            print(f"+++ {file_path} (formatted)")
                            orig_lines = original.split("\n")
                            fmt_lines = formatted.split("\n")
                            for i, (orig, fmt) in enumerate(zip(orig_lines, fmt_lines), 1):
                                if orig != fmt:
                                    print(f"- {i}: {orig}")
                                    print(f"+ {i}: {fmt}")
                else:
                    # Format mode
                    formatted = format_file(str(file_path), config, in_place=args.write)

                    if args.write:
                        print(f"✓ Formatted: {file_path}")
                    else:
                        # Print to stdout
                        if len(files_to_format) > 1:
                            print(f"\n=== {file_path} ===")
                        print(formatted)

            except Exception as e:
                print(f"Error formatting {file_path}: {e}", file=sys.stderr)
                if args.verbose:
                    import traceback

                    traceback.print_exc()
                return 1

        if args.check:
            print(f"\n✓ All {len(files_to_format)} files are formatted correctly")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for pyshort-fmt command."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Format PyShorthand files for consistency",
        epilog="Example: pyshort-fmt src/ --write",
    )
    parser.add_argument("input", help="Input .pys file or directory")
    parser.add_argument(
        "-w", "--write", action="store_true", help="Write changes in-place (default: print to stdout)"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check if files need formatting (don't modify)"
    )
    parser.add_argument("--diff", action="store_true", help="Show diff when using --check")
    parser.add_argument("--indent", type=int, default=2, help="Indentation spaces (default: 2)")
    parser.add_argument("--no-align", action="store_true", help="Don't align type annotations")
    parser.add_argument("--ascii", action="store_true", help="Use ASCII notation instead of Unicode")
    parser.add_argument(
        "--sort-state",
        choices=["location", "name", "none"],
        default="location",
        help="How to sort state variables (default: location)",
    )
    parser.add_argument(
        "--line-length", type=int, default=100, help="Maximum line length (default: 100)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()
    return format_command(args)


if __name__ == "__main__":
    sys.exit(main())
