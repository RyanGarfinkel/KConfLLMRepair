# KConf LLM Repair

## Getting Started

### 1. Setup
The following script installs package dependencies, sets up environment variables, clones the linux-next kernel, Z3, SuperC, and kmax, and installs python packages needed to run the scripts. Run the following from the root of this repository: ```/KConfLLMRepair```

```bash
sh  scripts/setup.sh
source ~/.bashrc
```

### 2. Environment Configuration
Create an```.env``` file in the ```/KConfLLMRepair``` directory for you Google Gemini API key. Then fill in the following information:

```env
GOOGLE_API_KEY=your-api-key-here
```

### 3. Base Configuration
The following script generates the base configuration used in this experiment. It also builds the linux-next kernel with this configuration then confirms it boots with QEMU.
```bash
sh scripts/generate_base_config.sh
```
The fololwing outputs the following files:
```
data/base/
├── base.config
├── build.log
└── qemu.log
```

### 4. Sample Generation
The following script generates ```n``` samples. Each sample contains a build log, change patch, klocalizer configuration, klocalizer log, and a QEMU log. ```n``` is an optional parameter which specifies how many samples to generate. By default, ```n=10```. A ```samples.csv``` file will be generated in the ```/base``` directory with information about each sample.
```bash
sh scripts/generate_samples.py --n 10
```  
The following adds to the file strcutre in ```/base/samples```:
```
data/base/samples
├── sample_0/
│   ├── build.log
│   ├── changes.patch
│   ├── klocalizer.config
│   ├── klocalizer.log
│   └── qemu.log
│
├── ...
│
├── sample_n/
│   ├── changes.patcs
│   ├── base.config
│   ├── base_qemu.log
│   ├── klocalizer.config
│   └── klocalizer_qemu.log
```

## How to Use
The following runs the repair on the samples previously generated. It takes one optional argument ```n```, which is the number of samples to repair. Please make sure there are enough samples within the ```/samples``` directory. By default, ```n=10```.
```bash
sh scripts/generate_repairs.py --n 10
```