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

| Option             | Required?          | Example                         | Description                                                      |
|--------------------|--------------------|---------------------------------|------------------------------------------------------------------|
| `--repair`         | :white_check_mark: | `--repair broken.config`        | Path to configuration file to repair.                            |
| `--output`         | :x:                | `--output workspace/sample`     | Path to log attempts and results. Default is CWD.                |
| `--src`            | :x:                | `--kernel-src $KERNEL_WORKTREE` | Path to the kernel source code. Default is $KERNEL_SRC variable. |
| `--model`          | :x:                | `--output workspace/sample_0`   | Model name of you wish to use for repair.                        |
| `--jobs`           | :x:                | `--jobs 8`                      | Number of jobs to run when building the kernel.                  |
| `--max-iterations` | :x:                | `--max-iterations 100`          | Maximum number of repair iterations per sample.                  |                              |

### Tools
| Tool                   | Args                                   | Description                                                |
|------------------------|----------------------------------------|------------------------------------------------------------|
| search_original_config | options: list[str]                     | Returns the values of the options from the original config.|
| search_latest_config   | options: list[str]                     | Returns the values of the options from the latest config.  |
| search_klocalizer_log  | regex: str                             | Returns pattern matches in the latest klocalizer log.      |
| search_build_log       | regex: str                             | Returns pattern matches in the latest build log.           |
| search_boot_log        | regex: str                             | Returns pattern matches in the latest QEMU boot log.       |

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

### Experiment Script (reccomended)

The `experiment.py` script handles sample generation and repair. Once each sample is generated, it will immediatly be passed into the repair process. You may opt to skip generation or repair. It is reccomended you run this script with the `--cleanup` flag to avoid having multiple worktrees at the end of this process.

```bash
python3 -m src.cli.experiment -n 25 --cleanup
```

Options & Flags
- `-n` Number of samples to generate. Default is 10.
- `-j` Number of jobs when building each sample. Default is 8.
- `--model` LLM to use during repair. Default is 'gemini-3-pro-preview'.
- `--max-iterations` Maximum number of attempts the repair agent has to alter the original configuration.
- `--max-threads` Max number of samples that can be generated at once. Default is 1.
- `--skip-generation` If present, will read samples from sampling.json and repair.
- `--skip-repair` If present, will only generate samples.
- `--cleanup` If present, will remove worktrees created after sampling and repair.

### Generating Samples

The `sample.py` script will generate `n` random configurations from the kernel source from the current commit. To run:
```bash
python3 -m scripts.cli.sample --cleanup
```

Options & Flags;
- `-n` Number of samples to generate. Default is 10.
- `-j` Number of jobs when building each sample. Default is 8.
- `--max-threads` Max number of samples that can be generated at once. Default is 1.
- `--cleanup` If present, will remove worktrees created after sampling.

### Repair

You may run the repair script on each sample generated by the `sample.py` script. See [instructions on how to run](#how-to-run) each commmand.


