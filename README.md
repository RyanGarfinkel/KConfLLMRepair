# KBootRepair

## Getting Started

The `setup.sh` script installs package dependencies, clones needed repositories, and installs python packages used to run the repair agent. The `activate.sh` script sets environment variables and the activates the python virtual environment.

```bash
bash setup.sh
source activate.sh
```

Please the follow the [.env.template](.env.template) to setup you `.env` file

## Agent Repair

See [the agent design](agent-design.png) to understand the repair process.

### How to Run

The repair script attempts to repair only one configuration at a time. See the [experiment section](#running-the-experiment) to repair more than one configuration at once. Additional options can be passed in to control the model used during the repair, amount of iterations, number of parallel jobs when building the kernel, and where to direct the output. See the table below. See the [output format](#output-format) for more information.

```bash
python3 -m src.cli.repair --repair broken.config --src $KERNEL_SRC
```

### Repair Options

| Option             | Required?          | Example                          | Description                                                       |
|--------------------|--------------------|----------------------------------|-------------------------------------------------------------------|
| `--repair`         | :white_check_mark: | `--repair broken.config`         | Path to configuration file to repair.                             |
| `--output`         | :x:                | `--output workspace/sample`      | Path to log attempts and results. Default is CWD.                 |
| `--src`            | :x:                | `--src $KERNEL_SRC`              | Path to the kernel source code. Default is $KERNEL_SRC variable.  |
| `--model`          | :x:                | `--model gemini-3-pro-preview`   | Model to use for repair. Default is `gemini-3-pro-preview`.       |
| `--jobs`           | :x:                | `--jobs 8`                       | Number of jobs to run when building the kernel. Default is 8.     |
| `--max-iterations` | :x:                | `--max-iterations 5`             | Maximum number of repair iterations. Default is 5.                |
| `--rag`            | :x:                | `--rag`                          | Use RAG semantic search tools instead of grep/chunk tools.        |
| `--arch` / `-a`    | :x:                | `--arch arm64`                   | Target architecture (`x86_64` or `arm64`). Defaults to `$ARCH`.  |

### Tools

The config search tools are always available. The grep/chunk tools are used by default; pass `--rag` to use the RAG tools instead.

| Tool                   | Args              | Description                                                 |
|------------------------|-------------------|-------------------------------------------------------------|
| search_original_config | options: list[str]| Returns the values of the options from the original config. |
| search_latest_config   | options: list[str]| Returns the values of the options from the latest config.   |
| grep_build_log         | pattern: str      | Returns lines from the build log matching the pattern.      |
| chunk_build_log        | line: int         | Returns lines from the build log centered around a line.    |
| grep_boot_log          | pattern: str      | Returns lines from the boot log matching the pattern.       |
| chunk_boot_log         | line: int         | Returns lines from the boot log centered around a line.     |

<details>
<summary>RAG Tools</summary>

These tools use embedding-based retrieval to semantically search logs. Passing `--rag` to the repair or experiment script enables them in place of the grep/chunk tools above.

| Tool             | Args        | Description                                               |
|------------------|-------------|-----------------------------------------------------------|
| search_build_log | query: str  | Returns relevant chunks from the build log for the query. |
| search_boot_log  | query: str  | Returns relevant chunks from the boot log for the query.  |

</details>

### Output Format
The `boot-agent` directory will be created in the output directory sepecified in the command (or the current working directory). The repaired configuration will be saved in `.config`. Information about the tools used and iteration summaries will be stored in `summary.json`.
```
agent-repair-attempts/
├── attempt_0/
├── attempt_#/
│   ├── boot.log
│   ├── build.log
│   ├── constraints.txt
│   ├── klocalizer.log
│   ├── modified.config
├── summary.json
├── repaired.config
├── agent-raw.json
```

## Running the Experiment

See my [Google Drive folder](https://drive.google.com/drive/u/1/folders/1jIB91vHjTCAGMrzhVpkVojy9UwUpXVOz) to see past samples and agent repairs.

### Experiment Script (recommended)

The `experiment.py` script handles sample generation and repair. Once each sample is generated, it will immediately be passed into the repair process. You may opt to skip generation or repair. It is recommended you run this script with the `--cleanup` flag to avoid leaving multiple worktrees behind.

```bash
python3 -m src.cli.experiment -n 25 --cleanup
```

| Option                 | Example                        | Description                                                        |
|------------------------|--------------------------------|--------------------------------------------------------------------|
| `-n`                   | `-n 25`                        | Number of samples to generate. Default is 10.                      |
| `--jobs` / `-j`        | `-j 8`                         | Number of parallel jobs for building kernels. Default is 8.        |
| `--model` / `-m`       | `--model gemini-3-pro-preview` | LLM to use during repair. Default is `gemini-3-pro-preview`.       |
| `--max-iterations`     | `--max-iterations 5`           | Maximum repair iterations per sample. Default is 5.                |
| `--max-threads` / `-t` | `-t 4`                         | Max samples generating concurrently. Default is 8.                 |
| `--skip-generation`    | `--skip-generation`            | Skip generation and repair existing samples from `sampling.json`.  |
| `--skip-repair`        | `--skip-repair`                | Only generate samples, skip repair.                                |
| `--cleanup`            | `--cleanup`                    | Remove worktrees after processing.                                 |
| `--rag`                | `--rag`                        | Use RAG semantic search tools instead of grep/chunk tools.         |
| `--arch` / `-a`        | `--arch arm64`                 | Target architecture (`x86_64` or `arm64`). Defaults to `$ARCH`.   |

### Generating Samples

The `sample.py` script generates `n` random configurations from the kernel source at the current commit.

```bash
python3 -m src.cli.sample -n 25 --cleanup
```

| Option                 | Example    | Description                                        |
|------------------------|------------|----------------------------------------------------|
| `-n`                   | `-n 25`    | Number of samples to generate. Default is 10.      |
| `--jobs` / `-j`        | `-j 8`     | Number of parallel jobs for building. Default is 8.|
| `--max-threads` / `-t` | `-t 4`     | Max samples generating concurrently. Default is 8. |
| `--cleanup`            | `--cleanup`| Remove worktrees after sampling.                   |

### Repair

You may run the repair script on each sample generated by `sample.py`. See [how to run](#how-to-run) for usage.
