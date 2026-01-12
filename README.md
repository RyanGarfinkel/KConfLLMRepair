# KConf LLM Boot Repair

## Getting Started

### 1. Setup 
The following script installs package dependencies, clones the linux-next kernel, Z3, SuperC, and kmax, and installs python packages needed to run the scripts. Run the following from the root of this repository: ```/KConfLLMRepair```

```bash
sh  setup.sh
```

### 2. Environment Configuration
Run the following to setup the environment varibles and activate the python virutal environment.
```bash
source activate.sh
```

Please also create an```.env``` file in the ```/KConfLLMRepair``` directory for you Google Gemini or OpenAI API key. Then fill in the following information:

```env
GOOGLE_API_KEY=your-api-key-here
OPENAI_API_KEY=your-api-key-here
```

### 3. Create Base Configuration
Run the following to create the base configuration in the ```config/``` directory. This base configuration is the defconfig merged with the kvm guest configuration for QEMU testing. Afterwards, the script builds and tests the configuration to confirm that it boots.
```bash
sh scripts/create_base.sh
```

You may use any base configuration as long as it follows the following format. It will be assumed that ```base.config``` is a bootable configuration. The ```.log``` files will be created by the script, but are not needed/used elsewhere.
```
config/
├── base.config # Must exist
├── build.log 
└── qemu.log
```

### 4. Generating Samples
Run the following to generate smaple configurations. You may pass in the following options to customize the number of samples generated and the commit size of each patch file created. By default, ```n=10``` and ```commit-window=250```.
```bash
python3 -m src.scripts.sample --n 10 --commit-window 250
```

The following files will be created by the script. ```summary.csv``` will contain metadata for each sample. Please keep these samples, as they are utilized during the Agent repair.
```
workspace/
├── samples
│   ├── summary.csv
│   ├── sample_#/
│   │   ├── build.log
│   │   ├── changes.patch
│   │   ├── klocalizer.config
│   │   ├── klocalizer.log
│   │   └── qemu.log
```

## LLM Agent Repair

### Tools
| Tool                  | Args               | Description                                               |   |   |
|-----------------------|--------------------|-----------------------------------------------------------|---|---|
| search_patch          | regex: str         | Returns pattern matches in the patch file.                |   |   |
| search_klocalizer_log | regex: str         | Returns pattern matches in the latest klocalizer log.     |   |   |
| search_build_log      | regex: str         | Returns pattern matches in the latest build log.          |   |   |
| search_qemu_log       | regex: str         | Returns pattern matches in the latest QEMU log.           |   |   |
| search_base_config    | options: list[str] | Returns the values of the options from the base config.   |   |   |
| search_latest_config  | options: list[str] | Returns the values of the options from the latest config. |   |   |

### How to Run
