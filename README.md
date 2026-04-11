# silentshell

"In my restless dreams, I see that environment." - Your Coding Agent

A thin wrapper that launches a coding agent inside a Docker container with your project mounted at `/project`. Gives your agent an isolated, reproducible environment — peace of mind while it runs in YOLO-mode.

## Prerequisites

- Python 3.11+
- Docker (running)

## Installation

1. Clone the repo:

   ```bash
   git clone https://github.com/souldzin/silentshell.git
   ```

2. Add a symlink to `silentshell.sh` somewhere on your `PATH` (e.g. `/usr/local/bin`):

   ```bash
   ln -s /path/to/silentshell/silentshell.sh /usr/local/bin/silentshell
   ```

3. Run `silentshell --help` to verify installation.

## Usage

```
silentshell <command> [options]
```

### `init`

Interactively create a `.silentshell.toml` for your project. Run this once before using `start`.

```bash
silentshell init                # init in current directory
silentshell init ~/my-project   # init in a specific directory
```

The wizard will ask for:

- **Agent template** — `claude` (Claude Code) or `pi` (pi coding agent)
- **Python project?** — adds `.venv` to `ignore-paths` and `PYTHONDONTWRITEBYTECODE` to env
- **Container/image name** — defaults to the project folder name
- **Dockerfile path** — where to copy the Dockerfile (defaults to `./config/silentshell.Dockerfile`)

### `start`

Launch the agent container. Requires a `.silentshell.toml` in the project directory (run `init` first).

```
silentshell start [options] [project_path] [-- agent_args...]
```

| Flag               | Description                                                      |
| ------------------ | ---------------------------------------------------------------- |
| `project_path`     | Directory to mount as `/project` (defaults to current directory) |
| `--build`          | Force rebuild of the Docker image                                |
| `--shell`          | Start a bash shell instead of the agent                          |
| `--exec CMD`       | Run a specific command non-interactively                         |
| `--no-interactive` | Disable TTY allocation                                           |
| `--no-setup`       | Skip the setup script defined in `.silentshell.toml`             |
| `--`               | Everything after this is forwarded to the agent                  |

**Examples:**

```bash
silentshell start                                  # mount current directory
silentshell start ~/my-project                     # mount a specific project
silentshell start --build ~/my-project             # rebuild image first
silentshell start --shell ~/my-project             # drop into a shell
silentshell start ~/my-project -- --resume         # pass flags to the agent
silentshell start --no-interactive --exec 'echo hello' ~/my-project
```

## Configuration

Place a `.silentshell.toml` in your project directory to configure the container:

```toml
# Optional: run this script inside the container before starting the agent
setup = "./scripts/setup.sh"

# Paths to shadow with empty tmpfs mounts (prevents host state leaking in)
ignore-paths = [".venv", "node_modules"]

[container]
name        = "myproject"               # persistent container name (omit for ephemeral)
image_name  = "myproject_dev_env"       # Docker image tag
image_dockerfile = "./config/claude.Dockerfile"
image_user  = "mary"                    # non-root user inside the container

[container.volumes]
"~/.claude"      = "/home/mary/.claude"       # persist agent config
"~/.claude.json" = "/home/mary/.claude.json"  # persist agent auth

[env]
MY_VAR = "some-value"   # environment variables injected into the container
```

> **Note:** All host paths in `[container.volumes]` must exist before running silentshell.
> Use `touch <path>` for files or `mkdir -p <path>` for directories.

### `ignore-paths`

Each entry is shadow-mounted as a `tmpfs` inside the container, preventing the host copy from leaking in. Glob patterns are supported (e.g. `".venv*"`). Useful for language-specific build artifacts that shouldn't bleed into the container environment.

### Container persistence

If `container.name` is set, silentshell reuses the container across runs (creating it on first run, restarting it if stopped). Outdated containers — those whose image or args hash has changed — are removed automatically. Omit `container.name` to always run ephemeral (`--rm`) containers.

## Dockerfiles

Two Dockerfile templates are bundled in `config/`. `silentshell init` copies the appropriate one into your project:

| Template                   | Agent                                                 |
| -------------------------- | ----------------------------------------------------- |
| `config/claude.Dockerfile` | [Claude Code](https://claude.ai/code)                 |
| `config/pi.Dockerfile`     | [pi coding agent](https://github.com/mariozechner/pi) |

## Running tests

**Init snapshot tests** (no Docker required):

```bash
./tests/test-init-claude.sh
./tests/test-init-pi.sh
```

These run `silentshell init` against a temp directory and compare the output to committed fixture files. Delete a fixture to regenerate it.

**Agent integration tests** (requires Docker):

```bash
./tests/test-agent-integration.sh          # uses existing image
./tests/test-agent-integration.sh --build  # rebuilds image first
```

These run inside the container and validate mounts, user, environment variables, tools, and the setup script.
