# KBootRepair

## Setup

### Prerequisites

- **Linux kernel** — v7.0-rc1
- **Go**
- **Syzkaller** ([repository](https://github.com/google/syzkaller))
- **KMax / KLocalizer** ([repository](https://github.com/paulgazz/kmax))
- **Z3** ([repository](https://github.com/Z3Prover/z3))
- **SuperC** ([repository](https://github.com/appleseedlab/superc))

### Environment Variables

```bash
export GOOGLE_API_KEY=your_api_key_here
export OPENAI_API_KEY=your_api_key_here
```

## Agent Repair

See [the agent design](agent-design.png) to understand the repair process.

### How to Run

Repairs a single configuration. See the [experiment section](#running-the-experiment) to repair multiple configurations at once.

```bash
python3 -m src.cli.repair --config broken.config
```

### Repair Options

| Option                | Description                                                         |
|-----------------------|---------------------------------------------------------------------|
| `--config`            | Path to configuration file to repair. *(required, or use patch mode below)* |
| `--original`          | Path to the original config. *(patch mode)*                         |
| `--modified`          | Path to the modified config. *(patch mode)*                         |
| `--patch`             | Path to the patch file. *(patch mode)*                              |
| `--output` / `-o`     | Path to write repair output. Default is CWD.                        |
| `--src`               | Path to kernel source. Defaults to `$KERNEL_SRC`.                   |
| `--img`               | Path to Debian QEMU image. Defaults to `$DEBIAN_IMG`.               |
| `--model` / `-m`      | LLM model to use. Default is `gemini-3.1-pro-preview`.              |
| `--jobs` / `-j`       | Parallel jobs for building the kernel. Default is 8.                |
| `--iterations` / `-i` | Maximum repair iterations. Default is 20.                           |
| `--arch` / `-a`       | Target architecture (`x86_64` or `arm64`). Defaults to `$ARCH`.    |
| `--rag`               | Use RAG semantic search tools instead of grep/chunk tools. *(experimental)* |

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
| grep_patch             | pattern: str      | Returns lines from the patch file matching the pattern. *(patch mode only)* |
| chunk_patch            | line: int         | Returns lines from the patch file centered around a line. *(patch mode only)* |

<details>
<summary>RAG Tools (experimental)</summary>

These tools use embedding-based retrieval to semantically search logs. Passing `--rag` to the repair or experiment script enables them in place of the grep/chunk tools above.

| Tool             | Args        | Description                                               |
|------------------|-------------|-----------------------------------------------------------|
| search_build_log | query: str  | Returns relevant chunks from the build log for the query. |
| search_boot_log  | query: str  | Returns relevant chunks from the boot log for the query.  |
| search_patch     | query: str  | Returns relevant chunks from the patch file for the query. |

</details>

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
| `--patch`              | Generate patch-based samples instead of random configs.   |
| `--since`              | Earliest commit date for patch samples. Default is `2020-01-01`. |
| `--commit-window`      | Commits between start and end commit for patches. Default is 500. |

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
| `--patch`              | Use patch-based samples instead of random configs.        |
