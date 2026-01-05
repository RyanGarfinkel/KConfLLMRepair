# KConf LLM Repair

## Dependencies
The following script will clone the Z3, linux-next, and Syzkaller repositories, copy an image of debian, then build the docker image:
```bash
sh scripts/setup.sh
```

## Running the environment
Run the docker container with the following command:
```bash
docker run --rm -it --privileged \
    -v "$(pwd):/workspace" \
    kconf-llm-repair
```

## Getting started
Run the following inside the Docker container from the ```/workspace``` directory:
### 1. Baseline configurations
```bash
python3 scripts/generate_baselines.py
```
The generate_baselines script will produce ```n``` base configurations and inital klocalizer repaired configurations. The following file structure will be created:
```
data/baselines/
├── sample_0/
│   ├── changes.patcs
│   ├── base.config
│   ├── base_qemu.log
│   └── klocalizer.config
│   └── klocalizer_qemu.log
│
├── ...
│
├── sample_n/
│   ├── changes.patcs
│   ├── base.config
│   ├── base_qemu.log
│   └── klocalizer.config
│   └── klocalizer_qemu.log
```

### 2. LLM Repair
```bash
```