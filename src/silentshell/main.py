#!/usr/bin/env python3
import argparse
import sys

from .version import get_version
from .constants import SCRIPT_NAME
from . import command_start, command_init, command_dockerfile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="Launch a coding agent inside an isolated Docker container.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=get_version())

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    command_start.build_parser(subparsers)
    command_init.build_parser(subparsers)
    command_dockerfile.build_parser(subparsers)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        # Re-parse with "start" prepended so argparse applies the start
        # subparser's argument schema (positional args, flags, etc.).
        # set_defaults alone won't do this — subparser arguments are only
        # recognised when the subcommand name is present in the input.
        args = parser.parse_args(["start"] + sys.argv[1:])

    if args.command == "start":
        command_start.run_start(args)
    elif args.command == "init":
        command_init.run_init(args)
    elif args.command == "dockerfile":
        command_dockerfile.run_dockerfile(args)
