import argparse
import os
import shutil
import sys
from pathlib import Path

from .constants import CONFIG_TOML_NAME, SCRIPT_DIR, SCRIPT_NAME

TEMPLATES = ["claude", "pi"]


def build_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "init",
        help=f"Interactively create a {CONFIG_TOML_NAME} for your project",
        description=f"Set up a {CONFIG_TOML_NAME} for your project.",
        epilog=(
            "Examples:\n"
            f"  {SCRIPT_NAME} init             # Init in current directory\n"
            f"  {SCRIPT_NAME} init ~/my-project  # Init in a specific directory"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Path to project directory to initialise (defaults to current directory)",
    )


def _prompt(question: str, default: str = "") -> str:
    """Prompt the user for input, showing the default in brackets."""
    if default:
        answer = input(f"{question} [{default}]: ").strip()
        return answer if answer else default
    return input(f"{question}: ").strip()


def _prompt_choice(question: str, choices: list[str], default: str) -> str:
    """Prompt the user to pick from a list of choices."""
    options = "/".join(c if c != default else c.upper() for c in choices)
    while True:
        answer = input(f"{question} [{options}]: ").strip().lower()
        if not answer:
            return default
        if answer in choices:
            return answer
        print(f"  Please enter one of: {', '.join(choices)}")


def _prompt_yes_no(question: str, default: bool = False) -> bool:
    """Prompt the user for a yes/no answer."""
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter y or n.")


def _build_toml(
    template: str,
    container_name: str,
    dockerfile_dest: str,
    is_python: bool,
) -> str:
    lines: list[str] = []

    if is_python:
        lines.append('ignore-paths = [".venv"]')
        lines.append("")

    lines.append("[container]")
    lines.append(f'name             = "{container_name}"')
    lines.append(f'image_name       = "{container_name}_silentshell_env"')
    lines.append(f'image_dockerfile = "{dockerfile_dest}"')
    lines.append('image_user       = "mary"')
    lines.append("")

    if template == "claude":
        lines.append("[container.volumes]")
        lines.append('"~/.claude"      = "/home/mary/.claude"')
        lines.append('"~/.claude.json" = "/home/mary/.claude.json"')
        lines.append("")
    elif template == "pi":
        lines.append("[container.volumes]")
        lines.append('"~/.pi" = "/home/mary/.pi"')
        lines.append("")

    if is_python:
        lines.append("[env]")
        lines.append('PYTHONDONTWRITEBYTECODE = "1"')
        lines.append("")

    return "\n".join(lines)


def run_init(args: argparse.Namespace) -> None:
    project_path = Path(args.project_path).resolve()

    if not project_path.is_dir():
        print(f"Error: Directory '{project_path}' does not exist.")
        sys.exit(1)

    config_file = project_path / CONFIG_TOML_NAME
    if config_file.is_file():
        print(f"{CONFIG_TOML_NAME} already exists in {project_path}.")
        print("Remove it first if you want to re-initialise.")
        sys.exit(1)

    print(f"Initialising silentshell in {project_path}\n")

    # --- Template ---
    template = _prompt_choice("Which agent template?", TEMPLATES, default="claude")

    # --- Python project ---
    is_python = _prompt_yes_no("Is this a Python project?", default=False)

    # --- Container / image name ---
    default_name = project_path.name
    container_name = _prompt("Container and image name", default=default_name)
    if not container_name:
        print("Error: Container name cannot be empty.")
        sys.exit(1)

    # --- Dockerfile destination ---
    dockerfile_dest = _prompt(
        "Dockerfile destination path", default="./config/silentshell.Dockerfile"
    )

    src_dockerfile = SCRIPT_DIR / "config" / f"{template}.Dockerfile"
    dest_dockerfile = (project_path / dockerfile_dest).resolve()
    dockerfile_ref = dockerfile_dest

    dest_dockerfile.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_dockerfile, dest_dockerfile)
    print(
        f"\n* Copied {template}.Dockerfile -> {dest_dockerfile.relative_to(project_path)}"
    )

    # --- Write .silentshell.toml ---
    toml_content = _build_toml(
        template=template,
        container_name=container_name,
        dockerfile_dest=dockerfile_ref,
        is_python=is_python,
    )
    config_file.write_text(toml_content)
    print(f"* Created {CONFIG_TOML_NAME}")

    print(f"\nAll set! Run 'silentshell start' to launch your agent.")
