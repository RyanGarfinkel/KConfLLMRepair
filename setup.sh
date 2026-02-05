#!/bin/bash
set -e

ROOT=$(pwd)

SKIP_DEPENDENCIES=false
if [ "$1" = "skip" ]; then
    SKIP_DEPENDENCIES=true
fi

# Dependency Installation
if [ "$SKIP_DEPENDENCIES" != "true" ]; then

    echo '[INFO] Installing dependencies...'

    sudo apt-get update
    sudo apt-get install -y \
        build-essential make gcc g++ \
        flex bison bc \
        libssl-dev libelf-dev libncurses-dev dwarves \
        python3 python3-dev python3-pip pipx lz4 \
        git wget unzip xz-utils lftp default-jdk \
        openjdk-8-jdk libz3-java libjson-java sat4j \
        qemu-system-x86 libdw-dev ccache \
        clang-15 llvm-15 lld-15 \
        gcc-x86-64-linux-gnu

    sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-15 100
    sudo update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-15 100
else
    echo '[ERROR] Cannot install dependencies. This script may fail. To prevent this, please manually install the required dependencies.'
fi

# Workspace Setup
echo '[INFO] Setting up the workspace directory...'

mkdir -p workspace/worktrees
mkdir -p workspace/images
mkdir -p workspace/tools

echo 'Workspace directrories created successfully.'

# Kernel Installation
if [ ! -d 'workspace/kernel' ]; then
    echo '[INFO] Cloning Linux Kernel...'
    git clone https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git workspace/kernel
    echo '[SUCCESS] Linux Kernel cloned successfully.'
else
    echo '[INFO] Linux Kernel already cloned at workspace/kernel'
    echo '[INFO] Pulling latest changes...'
    cd workspace/kernel
    git fetch origin
    git reset --hard origin/master
    echo '[SUCCESS] Linux Kernel updated successfully.'
    cd $ROOT
fi

# Debian Image Installation
if [ ! -f 'workspace/images/debian.raw' ]; then
    echo '[INFO] Downloading Debian image...'
    wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-nocloud-amd64.raw -O workspace/images/debian.raw
    echo '[SUCCESS] Debian image downloaded successfully.'
else
    echo '[INFO] Debian image already exists at workspace/images/debian.raw'
fi

# Clang Installation
if ! command -v clang &> /dev/null; then
    echo '[INFO] Installing Clang...'

    wget https://github.com/llvm/llvm-project/releases/download/llvmorg-17.0.6/clang+llvm-17.0.6-x86_64-linux-gnu-ubuntu-22.04.tar.xz -O clang.tar.xz
    tar -C ~/.local -xJf clang.tar.xz    
    mv ~/.local/clang+llvm-17.0.6-x86_64-linux-gnu-ubuntu-22.04 ~/.local/llvm
    rm clang.tar.xz

    export PATH=$HOME/.local/llvm/bin:$PATH
    echo '[SUCCESS] Clang installed successfully.'
else
    echo '[INFO] Clang is already installed.'
fi

# libdw-dev Installation
if [ ! -f /usr/include/elfutils/libdw.h ] && [ ! -f "$HOME/.local/include/elfutils/libdw.h" ]; then
    echo '[INFO] Installing libdw-dev...'

    wget https://sourceware.org/elfutils/ftp/0.191/elfutils-0.191.tar.bz2 -O elfutils-0.191.tar.bz2
    tar xf elfutils-0.191.tar.bz2
    cd elfutils-0.191

    ./configure --prefix=$HOME/.local --disable-debuginfod --disable-libdebuginfod
    make -j$(nproc)
    make install

    cd $ROOT
    rm -rf elfutils-0.191 elfutils-0.191.tar.bz2
    echo '[SUCCESS] libdw-dev installed successfully.'
else
    echo '[INFO] libdw-dev is already installed.'
fi

# Go Installation
if ! command -v go &> /dev/null; then
    echo '[INFO] Installing Go...'

    GO_VERSION=1.24.4
    GO_ARCH=amd64

    wget https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz -O go.tar.gz
    tar -C ~/.local -xzf go.tar.gz
    rm go.tar.gz

    echo '[SUCCESS] Go installed successfully.'
else
    echo '[INFO] Go is already installed.'
fi

# Syzkaller Installation & Build
if [ ! -d 'workspace/tools/syzkaller' ]; then
    echo '[INFO] Cloning and building Syzkaller...'
    git clone --depth 1 https://github.com/google/syzkaller.git workspace/tools/syzkaller
else
    echo '[INFO] Syzkaller already exists at workspace/tools/syzkaller'
fi

export GOROOT=$HOME/.local/go
export PATH=$PATH:$GOROOT/bin

cd workspace/tools/syzkaller
make
make kconf
cd $ROOT

# Z3 Installation
if [ ! -d 'workspace/tools/z3' ]; then
    echo '[INFO] Cloning and building Z3...'
    git clone --branch z3-4.8.17 --depth 1 https://github.com/Z3Prover/z3.git workspace/tools/z3
    cd workspace/tools/z3
    python3 scripts/mk_make.py --java
    cd build
    make -j$(nproc)
    echo '[SUCCESS] Z3 cloned and built successfully.'
    cd $ROOT
else
    echo '[INFO] Z3 already exists at workspace/tools/z3'
fi

# SuperC Installation
if [ ! -d 'workspace/tools/superc' ]; then
    mkdir -p workspace/tools/superc
    cd workspace/tools/superc
    echo '[INFO] Cloning and building SuperC...'
    wget -O - https://raw.githubusercontent.com/appleseedlab/superc/master/scripts/install.sh | bash
    echo '[SUCCESS] SuperC cloned and built successfully.'
    cd $ROOT
else
    echo '[INFO] SuperC already exists at workspace/tools/superc'
fi

# Python Virtual Environment Setup
echo '[INFO] Setting up Python virtual environment...'
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo '[SUCCESS] Virtual environment created successfully.'
else
    echo '[INFO] Virtual environment already exists.'
fi

. venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo '[SUCCESS] Python dependencies installed successfully.'

# Finish
echo '[SUCCESS] Setup complete.'
echo '[INFO] Run source activate.sh to activate the virtual environment and set up the environment variables.'
