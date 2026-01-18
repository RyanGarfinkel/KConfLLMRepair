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

### Repair Options
| Option             | Required? | Example                         | Description                                                                                                                  |
|--------------------|-----------|---------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `--base`           | - [x]     | `--base base.config`            | Path to original configuration.                                                                                              |
| `--modified`       | - [x]     | `--modified modified.config`    | Path to modified configuration.                                                                                              |
| `--patch`          | - [x]     | `--patch changes.patch`         | Path to file/patch klocalizer should target.                                                                                 |
| `--output`         | - [ ]     | `--output workspace/sample_0`   | Path where agent-repair directory will be created. By default, this is the current working directory.                        |
| `--kernel-src`     | - [ ]     | `--kernel-src $KERNEL_WORKTREE` | Path to kernel source. By default, this looks for $KERNEL_SRC environment variable.                                          |
| `--model`          | - [ ]     | `--model gpt-4o-mini`           | Sets which model the agent should use. If empty, gemini-3-pro-preview or                                                     |
| `--max-iterations` | - [ ]     | `--max-iterations 10`           | Sets the maximum amount of tries the agent has to apply and test changes to the configuration. By default, this is set to 5. |
| `--jobs`           | - [ ]     | `--jobs 8`                      | Sets the number of jobs to run when building the kernel image. By default, this is set to 8.                                 |

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
boot-agent/
├── attempt_0/
├── attempt_#/
│   ├── build.log
│   ├── changes.patch
│   ├── changes.patch.kloc_targets
│   ├── klocalizer.log
│   ├── modified.config
├── .config
├── summary.json
```

## Generating Samples
