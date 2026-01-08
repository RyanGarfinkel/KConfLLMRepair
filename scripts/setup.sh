#!/bin/bash

set -e

WORKING_DIR=$(pwd)

# ENV Variables
echo 'export ARCH=x86_64' >> ~/.bashrc
echo 'export CROSS_COMPILE=x86_64-linux-gnu-' >> ~/.bashrc
echo 'export KERNEL_SRC=$HOME/kernel' >> ~/.bashrc
echo 'export SYZKALLER_SRC=$HOME/syzkaller' >> ~/.bashrc
echo 'export Z3_SRC=$HOME/z3' >> ~/.bashrc
echo 'export WORKSPACE=$WORKING_DIR' >> ~/.bashrc

export ARCH=x86_64
export CROSS_COMPILE=x86_64-linux-gnu-
export KERNEL_SRC=$HOME/kernel
export SYZKALLER_SRC=$HOME/syzkaller
export Z3_SRC=$HOME/z3
export WORKSPACE=$WORKING_DIR

# Installing dependencies
echo "Installing dependencies..."

sudo apt-get update
sudo apt-get install -y \
     build-essential make gcc g++ \
     flex bison bc \
     libssl-dev libelf-dev libncurses-dev dwarves \
     python3 python3-dev python3-pip pipx \
     git wget unzip xz-utils lftp default-jdk \
     openjdk-8-jdk libz3-java libjson-java sat4j \
     qemu-system-x86 libdw-dev ccache \
     clang-15 llvm-15 lld-15 \
     gcc-x86-64-linux-gnu

sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-15 100
sudo update-alternatives --install /usr/bin/ld.lld ld.lld /usr/bin/ld.lld-15 100

# Go installation
echo "Installing Go..."

GO_VERSION=1.24.4
GO_ARCH=amd64

wget https://go.dev/dl/go${GO_VERSION}.linux-${GO_ARCH}.tar.gz

sudo tar -C /usr/local -xzf go${GO_VERSION}.linux-${GO_ARCH}.tar.gz
rm go${GO_VERSION}.linux-${GO_ARCH}.tar.gz

echo 'export GOROOT=/usr/local/go' >> ~/.bashrc
echo 'export PATH=$PATH:$GOROOT/bin' >> ~/.bashrc

export GOROOT=/usr/local/go
export PATH=$PATH:$GOROOT/bin

# Linux Kernel
echo "Cloning Linux Kernel..."
git clone https://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git $KERNEL_SRC

# Syzkaller
echo "Cloning and building Syzkaller..."
git clone https://github.com/google/syzkaller.git $SYZKALLER_SRC
cd $SYZKALLER_SRC
make

echo 'export PATH=$SYZKALLER_SRC/bin:$PATH' >> ~/.bashrc
export PATH=$SYZKALLER_SRC/bin:$PATH

cd $WORKING_DIR

# Z3
echo "Cloning and building Z3..."
git clone --branch z3-4.8.17 --depth 1 https://github.com/Z3Prover/z3.git $Z3_SRC
cd $Z3_SRC
python3 scripts/mk_make.py --java
cd build
make -j$(nproc)

echo 'export CLASSPATH=/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$Z3_SRC/build:$LD_LIBRARY_PATH' >> ~/.bashrc

export CLASSPATH=/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH
export LD_LIBRARY_PATH=$Z3_SRC/build:$LD_LIBRARY_PATH


cd $WORKING_DIR

# SuperC
echo "Cloning and building SuperC..."
cd ~
wget -O - https://raw.githubusercontent.com/appleseedlab/superc/master/scripts/install.sh | bash

echo 'export CLASSPATH=$HOME/.local/share/superc/superc.jar:$HOME/.local/share/superc/xtc.jar:$HOME/.local/share/superc/JavaBDD/javabdd-1.0b2.jar:/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH' >> ~/.bashrc
export CLASSPATH=$HOME/.local/share/superc/superc.jar:$HOME/.local/share/superc/xtc.jar:$HOME/.local/share/superc/JavaBDD/javabdd-1.0b2.jar:/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH

# Python packages
echo "Installing Python packages..."
cd $WORKING_DIR
pipx install kmax
pipx ensurepath

python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install -r requirements.txt --break-system-packages

source ~/.bashrc

echo "Setup complete"
echo ""
echo "Run the following command to run the kmax tools:"
echo "source ~/.bashrc"
