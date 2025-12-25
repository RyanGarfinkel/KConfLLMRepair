# KConf LLM Repair

## Installing Dependencies

You can run ```sh scripts/setup.sh``` or

### 1. SuperC
```bash
git clone https://github.com/appleseedlab/superc.git
```

### 2. Z3 (specific version for Java 8)
```bash
git clone https://github.com/Z3Prover/z3.git
cd z3
git checkout d95805b6311b357ce37417db24c9fc948dc8f772
```

### 3. kmax
```bash
git clone https://github.com/paulgazz/kmax.git
```

### 4. linux-next
```bash
git clone git://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git kernel
```

### 5. syzkaller
```bash
git clone https://github.com/google/syzkaller
```

## Docker Envirornment

### 1. Build Docker Container
```bash
docker build -t kconf-llm-repair . 
```

### 2. Run Docker Container
```bash
docker run -v "$(pwd):/workspace" -it kconf-llm-repair
```