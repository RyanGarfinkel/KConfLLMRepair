# KConf LLM Boot Repair

## Getting Started

The `setup.sh` script installs package dependencies, clones needed repositories, and installs python packages used to run the repair agent. The `activate.sh` script sets environment variables and the activates the python virtual environment.

```bash
bash setup.sh
source activate.sh
```

Please the follow the [.env.template](.env.template) to setup you `.env` file

## Agent Repair

### How to Run

The repair script attempts to repair only one configuration at a time. See the [experiment section](#running-the-experiment) to repair more than one configuration at once. Additional options can be passed in to control the model used during the repair, amount of iterations, number of parallel jobs when building the kernel, and where to direct the output. See the table below. See the [output format](#output-format) for more information.

```bash
python3 -m src.scripts.repair --base base.config --modified modified.config --patch changes.patch --kernel-src $KERNEL_SRC
```

### Repair Options
| Option             | Required?          | Example                         | Description                                                                                                                  |
|--------------------|--------------------|---------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `--base`           | :white_check_mark: | `--base base.config`            | Path to original configuration.                                                                                              |
| `--modified`       | :white_check_mark: | `--modified modified.config`    | Path to modified configuration.                                                                                              |
| `--patch`          | :white_check_mark: | `--patch changes.patch`         | Path to file/patch klocalizer should target.                                                                                 |
| `--output`         | :x:                | `--output workspace/sample_0`   | Path where agent-repair directory will be created. By default, this is the current working directory.                        |
| `--kernel-src`     | :x:                | `--kernel-src $KERNEL_WORKTREE` | Path to kernel source. By default, this looks for $KERNEL_SRC environment variable.                                          |
| `--model`          | :x:                | `--model gpt-4o-mini`           | Sets which model the agent should use. If empty, gemini-3-pro-preview or                                                     |
| `--max-iterations` | :x:                | `--max-iterations 10`           | Sets the maximum amount of tries the agent has to apply and test changes to the configuration. By default, this is set to 5. |
| `--jobs`           | :x:                | `--jobs 8`                      | Sets the number of jobs to run when building the kernel image. By default, this is set to 8.                                 |

### Tools
| Tool                  | Args                                   | Description                                               |
|-----------------------|----------------------------------------|-----------------------------------------------------------|
| search_patch          | regex: str                             | Returns pattern matches in the patch file.                |
| search_klocalizer_log | regex: str                             | Returns pattern matches in the latest klocalizer log.     |
| search_build_log      | regex: str                             | Returns pattern matches in the latest build log.          |
| search_qemu_log       | regex: str                             | Returns pattern matches in the latest QEMU log.           |
| search_base_config    | options: list[str]                     | Returns the values of the options from the base config.   |
| search_latest_config  | options: list[str]                     | Returns the values of the options from the latest config. |
| apply_and_test        | define: list[str], undefine: list[str] | Reruns klocalizer with changes then tests if it boots.    |

### Output Format
The `boot-agent` directory will be created in the output directory sepecified in the command (or the current working directory). The repaired configuration will be saved in `.config`. Information about the tools used and iteration summaries will be stored in `summary.json`.
```
agent-repair-attempts/
├── attempt_0/
├── attempt_#/
│   ├── build.log
│   ├── changes.patch
│   ├── changes.patch.kloc_targets
│   ├── klocalizer.log
│   ├── modified.config
│   ├── info.json
├── .config
├── summary.json
```

## Running the Experiment

See my [Google Drive folder](https://drive.google.com/drive/u/1/folders/1jIB91vHjTCAGMrzhVpkVojy9UwUpXVOz) to see past samples and agent repairs.

### Generating Samples

The `generate_samples.py` script uses syzkaller's syz-kconf tool to generate the base configuration. Patches are randomly selected from all of the linux-next's commits from the latest commit to commits as early as `01/01/2020`.

Optional Parameters;
- `--n` Number of samples to generate. Default is 10.
- `--commit-window` Number of commits to include in each patch. Default is 250.
- `--max-threads` Max number of samples that can be generated at once. Default is 1.
- `--jobs` Number of jobs when building each sample. Default is 8.

### Repair All


