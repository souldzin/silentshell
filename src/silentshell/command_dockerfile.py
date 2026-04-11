import argparse
import sys

from .constants import SCRIPT_DIR, SCRIPT_NAME

BUNDLED_TEMPLATES = ["example", "claude", "pi"]


def build_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "dockerfile",
        help="Print a bundled Dockerfile template to stdout",
        description="Print a bundled Dockerfile template to stdout.",
        epilog=(
            "Examples:\n"
            f"  {SCRIPT_NAME} dockerfile example        # print the example template\n"
            f"  {SCRIPT_NAME} dockerfile claude         # print the claude template\n"
            f"  {SCRIPT_NAME} dockerfile pi             # print the pi template"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "template",
        choices=BUNDLED_TEMPLATES,
        metavar="template",
        help=f"template to print: {', '.join(BUNDLED_TEMPLATES)}",
    )


def run_dockerfile(args: argparse.Namespace) -> None:
    dockerfile = SCRIPT_DIR / "config" / f"{args.template}.Dockerfile"

    if not dockerfile.is_file():
        print(f"Error: bundled template '{args.template}' not found at {dockerfile}")
        sys.exit(1)

    print(dockerfile.read_text(), end="")
