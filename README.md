# KBootRepair

## Setup

### Install

`setup.sh` installs system dependencies and builds all required tooling:

- **Linux kernel** — v7.0-rc1
- **Go**
- **Syzkaller** ([repository](https://github.com/google/syzkaller))
- **KMax / KLocalizer** ([repository](https://github.com/paulgazz/kmax), branch `dev/klocalizer-add-check-mutex`)
- **Z3** ([repository](https://github.com/Z3Prover/z3))
- **SuperC** ([repository](https://github.com/appleseedlab/superc))

It also clones the kernel, builds the Debian QEMU boot images, and creates a Python virtual environment (`venv`) with `requirements.txt` installed.

```bash
./setup.sh
```

### Activate

`activate.sh` activates `venv` and exports the environment variables the rest of the tooling depends on (`KERNEL_SRC`, `DEBIAN_IMG`, `ARCH`, build toolchain paths, etc.).

```bash
source activate.sh
```

### API Keys

Export an API key for whichever model provider you plan to use:

```bash
export GOOGLE_API_KEY=your_api_key_here
```

## Agent Repair

See [the agent design](agent-design.png) to understand the repair process.

### How to Run

Repairs a single configuration. See the [experiment section](#running-the-experiment) to repair multiple configurations at once.

```bash
python3 -m src.cli.repair --config broken.config
```

To quickly test KBootRepair, set `--iterations 2`.

### Repair Options

| Option                | Description                                                         |
|-----------------------|---------------------------------------------------------------------|
| `--config`            | Path to configuration file to repair. *(required)*                  |
| `--output` / `-o`     | Path to write repair output. Default is CWD.                        |
| `--src`               | Path to kernel source. Defaults to `$KERNEL_SRC`.                   |
| `--img`               | Path to Debian QEMU image. Defaults to `$DEBIAN_IMG`.               |
| `--model` / `-m`      | LLM model to use. Default is `gemini-3.1-pro-preview`.              |
| `--jobs` / `-j`       | Parallel jobs for building the kernel. Default is 8.                |
| `--iterations` / `-i` | Maximum repair iterations. Default is 20.                           |
| `--arch` / `-a`       | Target architecture (`x86_64` or `arm64`). Defaults to `$ARCH`.    |

### Tools

| Tool                   | Args              | Description                                                 |
|------------------------|-------------------|-------------------------------------------------------------|
| search_original_config | options: list[str]| Returns the values of the options from the original config. |
| search_latest_config   | options: list[str]| Returns the values of the options from the latest config.   |
| grep_build_log         | pattern: str      | Returns lines from the build log matching the pattern.      |
| chunk_build_log        | line: int         | Returns lines from the build log centered around a line.    |
| grep_boot_log          | pattern: str      | Returns lines from the boot log matching the pattern.       |
| chunk_boot_log         | line: int         | Returns lines from the boot log centered around a line.     |

### Output Format

An `agent_repair/` directory is created inside the output path (defaults to CWD). If repair succeeds, `repaired.config` is written there.

```
agent_repair/
├── attempt_0/
│   ├── build.log
│   └── boot.log
├── attempt_N/
│   ├── raw-agent-response.json
│   ├── constraints.txt
│   ├── klocalizer.log
│   ├── modified.config
│   ├── build.log
│   └── boot.log
├── summary.json
└── repaired.config
```

## Running the Experiment

Samples and results are organized by architecture under `workspace/samples/{arch}/`. Run the two scripts in order:

### Step 1 — Generate Samples

```bash
python3 -m src.cli.sample -n 25 --arch x86_64 --cleanup
```

Samples are saved to `workspace/samples/{arch}/sample_{i}/` with a `sampling.json` index in that directory.

| Option                 | Description                                               |
|------------------------|-----------------------------------------------------------|
| `-n`                   | Number of samples to generate. Default is 10.             |
| `--arch` / `-a`        | Target architecture (`x86_64` or `arm64`).                |
| `--jobs` / `-j`        | Parallel jobs for building. Default is 8.                 |
| `--max-threads` / `-t` | Max samples generating concurrently. Default is 1.        |
| `--cleanup`            | Remove worktrees after sampling.                          |

### Step 2 — Run Experiment

```bash
python3 -m src.cli.experiment --arch x86_64
```

Reads `workspace/samples/{arch}/sampling.json` and repairs each sample in parallel. After each repair completes, reads its `summary.json` and updates `results.json` in the output directory.

| Option                 | Description                                               |
|------------------------|-----------------------------------------------------------|
| `--arch` / `-a`        | Target architecture. Default is `x86_64`.                 |
| `--model` / `-m`       | LLM to use during repair. Default is `gemini-3.1-pro-preview`. |
| `--jobs` / `-j`        | Parallel jobs for building kernels. Default is 8.         |
| `--threads` / `-t`     | Samples repaired in parallel. Default is 1.               |
| `--iterations` / `-i`  | Max repair iterations per sample. Default is 20.          |

### LLM Case Study

One-shot approach, passing the entire configuration file, build log, and boot log into the LLM.

```bash
python3 -m src.cli.naive --config broken.config --build-log build.log --boot-log boot.log
```

To run the baseline over an existing sample set (requires `sampling.json` from the [sampling step](#step-1--generate-samples)):

```bash
python3 -m src.cli.naive_experiment --arch x86_64
```