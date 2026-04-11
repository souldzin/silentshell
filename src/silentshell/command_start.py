import argparse
import os
import shlex
import sys
import hashlib
from pathlib import Path

from . import docker
from .constants import CONFIG_TOML_NAME, SCRIPT_NAME
from .config import Config, load_config
from .execute import get_execution_strategy


def build_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "start",
        help="Launch a Docker container with the project directory mounted",
        description="Launch a Docker container with project directory mounted.",
        epilog=(
            "Any arguments after -- are forwarded as args to the Docker command.\n\n"
            "Examples:\n"
            f"  {SCRIPT_NAME} start                                # Mount current directory\n"
            f"  {SCRIPT_NAME} start ~/my-project                   # Mount specific project\n"
            f"  {SCRIPT_NAME} start --build ~/project              # Rebuild image and mount project\n"
            f"  {SCRIPT_NAME} start --exec /bin/sh ~/project       # Start shell in container\n"
            f"  {SCRIPT_NAME} start ~/project -- --model gpt-4     # Pass --model gpt-4 to the cmd\n"
            f"  {SCRIPT_NAME} start --no-interactive --exec 'echo hello' ~/project"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=os.getcwd(),
        help="Path to project directory to mount (defaults to current directory)",
    )
    parser.add_argument(
        "--build", action="store_true", help="Force rebuild of Docker image"
    )
    parser.add_argument(
        "--exec",
        metavar="CMD",
        help="Execute specific command in the container",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive mode (no TTY allocation)",
    )
    parser.add_argument(
        "--no-setup",
        action="store_true",
        help=f"Skip running the setup command specified in {CONFIG_TOML_NAME}",
    )
    parser.add_argument(
        "cmd_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the command (after --)",
    )


def hash_list(values: list[str]) -> str:
    raw = "|".join(values).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_image(config: Config):
    dockerfile = config.container.image_dockerfile
    if not dockerfile:
        print(
            "Error: container.image_dockerfile not found in config. This is required to build the image."
        )
        sys.exit(1)

    if not dockerfile.is_file():
        print(f"Error: Dockerfile not found at {dockerfile}")
        print(f"Please ensure the Dockerfile path in {CONFIG_TOML_NAME} is correct.")
        sys.exit(1)

    if not config.container.image_name:
        print(
            "Error: container.image_name not found in config. This is required to build the image."
        )
        sys.exit(1)

    docker.build_image(
        image_name=config.container.image_name,
        dockerfile=str(dockerfile),
        context_dir=str(config.context.project_path),
    )

    print("* Docker image built successfully")

    return docker.get_image(config.container.image_name)


def get_volume_args(config: Config, home_path: Path) -> list[str]:
    result = []

    for k, v in config.container.volumes.items():
        host_path = Path(k.replace("~", str(home_path)))
        if not host_path.exists():
            hint = f"touch {host_path}" if host_path.suffix else f"mkdir -p {host_path}"
            print(f"Error: Volume host path '{host_path}' does not exist.")
            print(f"Please create it first:  {hint}")
            sys.exit(1)
        print(f"* Mounting: {host_path} -> {v}")
        result.append("-v")
        result.append(f"{host_path}:{v}")

    return result


def get_ignore_path_args(
    config: Config, container_uid: int = 1000, container_gid: int = 1000
) -> list[str]:
    volume_args: list[str] = []
    project_path = config.context.project_path

    for p in config.ignore_paths:
        clean = p.strip("/")
        if not clean:
            continue

        matched = sorted(project_path.glob(clean))
        if matched:
            targets = [m.relative_to(project_path) for m in matched if m.is_dir()]
        else:
            targets = [Path(clean)]

        for rel in targets:
            container_path = f"/project/{rel}"
            print(f"* Ignoring path: {container_path}")
            volume_args.extend(
                [
                    "--tmpfs",
                    f"{container_path}:exec,uid={container_uid},gid={container_gid}",
                ]
            )
    return volume_args


def get_docker_cmd(args: argparse.Namespace, config: Config) -> list[str]:
    image_cmd = docker.get_cmd_for_image(config.container.image_name)

    should_run_setup = config.setup_script and not args.no_setup

    if getattr(args, "exec", None):
        main_cmd = args.exec
        print(f"* Executing: {args.exec}")
    elif not args.cmd_args and not should_run_setup:
        return []
    else:
        main_cmd = " ".join([*image_cmd, *(shlex.quote(arg) for arg in args.cmd_args)])
        if args.cmd_args:
            print(f"* Starting silentshell with args: {' '.join(args.cmd_args)}")
        else:
            print("* Starting silentshell...")

    if should_run_setup:
        print(f"* Setup command: {config.setup_script}")
        full_cmd = f"{config.setup_script} && {main_cmd}"
    else:
        full_cmd = main_cmd

    return ["sh", "-c", full_cmd]


def get_env_args(config: Config) -> list[str]:
    result = [
        "-e",
        f"HOME=/home/{config.container.image_user}",
    ]

    for k, v in config.env.items():
        result.append("-e")
        result.append(f"{k}={v}")

    return result


def run_start(args: argparse.Namespace) -> None:
    # REMAINDER captures a leading "--" separator; strip it.
    if args.cmd_args and args.cmd_args[0] == "--":
        args.cmd_args = args.cmd_args[1:]

    project_path = Path(args.project_path).resolve()
    home = Path.home().resolve()

    if not project_path.is_dir():
        print(f"Error: Directory '{project_path}' does not exist")
        sys.exit(1)

    if project_path == home or home.is_relative_to(project_path):
        print(f"Error: Refusing to mount '{project_path}' as the project directory.")
        print(
            "Mounting your home directory (or a parent) into the container can cause "
            "file locks, inotify storms, and freeze running programs."
        )
        print(
            "Please run from a specific project directory, or pass one as an argument."
        )
        sys.exit(1)

    if project_path == Path("/"):
        print("Error: Refusing to mount '/' as the project directory.")
        print("Please specify a specific project directory.")
        sys.exit(1)

    # Guard: require .silentshell.toml
    config_file = project_path / CONFIG_TOML_NAME
    if not config_file.is_file():
        print(f"Error: No {CONFIG_TOML_NAME} found in {project_path}.")
        print(f"Run 'silentshell init' to set one up.")
        sys.exit(1)

    if not docker.docker_is_running():
        print("Error: Docker is not running or not accessible")
        print("Please start Docker and try again")
        sys.exit(1)

    config = load_config(project_path)

    docker_image = docker.get_image(config.container.image_name)

    if args.build or not docker_image:
        print("* Building Docker image...")
        docker_image = build_image(config)

    if not docker_image:
        print(f"Error: Could not find docker image {config.container.image_name}.")
        sys.exit(1)

    interactive = not args.no_interactive
    docker_cmd = get_docker_cmd(args, config)

    container_uid, container_gid = docker.get_container_uid_gid(
        config.container.image_name, user=config.container.image_user
    )
    ignore_volume_args = get_ignore_path_args(config, container_uid, container_gid)
    volume_args = get_volume_args(config, home_path=home)
    env_args = get_env_args(config)

    print(f"* Mounting: {project_path} -> /project")

    sys.stdout.flush()

    docker_args: list[str] = [
        *(["-i", "-t"] if interactive else []),
        "-v",
        f"{project_path}:/project",
        *ignore_volume_args,
        *volume_args,
        *env_args,
        "-w",
        "/project",
        config.container.image_name,
        *docker_cmd,
    ]
    runtime_hash = hash_list(["IMAGE", docker_image.id, "ARGS", *docker_args])[:8]
    strategy = get_execution_strategy(config, runtime_hash)

    result = strategy.execute(docker_args)
    retcode = result.get_return_code()

    if retcode == 0:
        print("[silentshell ending: Leave]")
    else:
        print("[silentshell ending: In Water]")

    sys.exit(retcode)
