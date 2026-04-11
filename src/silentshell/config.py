from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import CONFIG_TOML_NAME

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


class ConfigError(Exception):
    _message: str

    def __init__(self, message: str):
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message

    def __str__(self):
        return f"[ConfigError] {self.message}"


@dataclass(frozen=True)
class ConfigContext:
    project_path: Path
    config_toml_path: Path | None


@dataclass(frozen=True)
class ContainerConfig:
    name: str | None
    image_name: str
    image_dockerfile: Path | None
    image_user: str
    volumes: dict[str, str]

    @staticmethod
    def try_parse(context: ConfigContext, values: dict[str, Any]) -> "ContainerConfig":
        config_path = context.config_toml_path

        name = values.get("name", "")
        image_name = values.get("image_name", "")
        image_dockerfile_str = values.get("image_dockerfile", "")
        image_user = values.get("image_user", "")
        volumes = values.get("volumes", {})

        image_dockerfile: Path | None = None

        if not isinstance(name, str):
            name = None

        if not isinstance(image_name, str):
            image_name = ""

        if not isinstance(image_user, str):
            image_user = ""

        if not isinstance(volumes, dict):
            volumes = {}

        if (
            isinstance(image_dockerfile_str, str)
            and image_dockerfile_str
            and config_path
        ):
            config_dir_path = config_path.parent
            image_dockerfile = (config_dir_path / Path(image_dockerfile_str)).resolve()

        return ContainerConfig(
            name=name,
            image_name=image_name,
            image_dockerfile=image_dockerfile,
            image_user=image_user,
            volumes=volumes,
        )


@dataclass(frozen=True)
class Config:
    context: ConfigContext

    container: ContainerConfig
    env: dict[str, str]
    setup_script: str
    ignore_paths: list[str]

    @staticmethod
    def try_parse(context: ConfigContext, values: dict[str, Any]) -> "Config":
        container_values = values.get("container", {})
        env_args = values.get("env", {})
        setup = values.get("setup", "")
        ignore_paths = values.get("ignore-paths", [])

        if not isinstance(container_values, dict):
            container_values = {}

        if not isinstance(env_args, dict):
            env_args = {}

        if not isinstance(setup, str):
            setup = ""

        if not isinstance(ignore_paths, list):
            ignore_paths = []

        return Config(
            context=context,
            ignore_paths=ignore_paths,
            setup_script=setup,
            env=env_args,
            container=ContainerConfig.try_parse(context, container_values),
        )


def load_config(project_path: Path) -> Config:
    config_file = project_path / CONFIG_TOML_NAME

    if not config_file.is_file():
        return Config.try_parse(
            ConfigContext(project_path=project_path, config_toml_path=None), {}
        )

    if tomllib is None:
        print(
            f"Warning: {CONFIG_TOML_NAME} found but no TOML parser available. "
            "Upgrade to Python ≥ 3.11 or install 'tomli'."
        )

        return Config.try_parse(
            ConfigContext(project_path=project_path, config_toml_path=None), {}
        )

    with open(config_file, "rb") as f:
        config_values = tomllib.load(f)

    context = ConfigContext(project_path=project_path, config_toml_path=config_file)
    return Config.try_parse(context, config_values)
