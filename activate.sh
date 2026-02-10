#!/bin/bash

ROOT=$(pwd)

# Python Virtual Environment Activation
if [ -f 'venv/bin/activate' ]; then
    echo '[INFO] Activating Python virtual environment...'
    . venv/bin/activate
    echo '[SUCCESS] Virtual environment activated successfully.'
else
    echo '[ERROR] Virtual environment not found. Please run setup.sh to create it.'
    return 1
fi

echo '[INFO] Setting environment variables...'

export PROJECT_ROOT=$ROOT

# Core Settings
export KERNEL_SRC=$ROOT/workspace/kernel
export BASE_CONFIG=$ROOT/config/base.config ###
export SAMPLE_DIR=$ROOT/workspace/samples
export WORKTREE_DIR=$ROOT/workspace/worktrees

# Build Settings
export CROSS_COMPILE=x86_64-linux-gnu-
export DEBIAN_IMG=$ROOT/workspace/images/debian.raw #$ROOT/workspace/images/bullseye.img 
export GOROOT=$HOME/.local/go
export ARCH=x86_64

# Tool Settings
export SUPERC_PATH=$HOME/.local/bin/superc_linux.sh
export Z3_SRC=$ROOT/workspace/tools/z3

# Syzkaller Settings
# export UPSTREAM_APPARMOR_KASAN_CONFIG=$ROOT/workspace/tools/syzkaller/dashboard/config/linux/upstream-apparmor-kasan.config
export SYZKALLER_SRC=$ROOT/workspace/tools/syzkaller
export SYZ_KCONF=$ROOT/workspace/tools/syzkaller/bin/syz-kconf
export MAIN_YML=$ROOT/workspace/tools/syzkaller/dashboard/config/linux/main.yml

# Dependency Settings
export CLASSPATH=$HOME/.local/share/superc/superc.jar:$HOME/.local/share/superc/xtc.jar:$HOME/.local/share/superc/JavaBDD/javabdd-1.0b2.jar:/usr/share/java/org.sat4j.core.jar:/usr/share/java/json.jar:$Z3_SRC/build/com.microsoft.z3.jar:$CLASSPATH
export LD_LIBRARY_PATH=$Z3_SRC/build:$LD_LIBRARY_PATH
export PATH=/usr/lib/ccache:$GOROOT/bin:$PATH
export PATH=$HOME/.local/llvm/bin:$PATH

export C_INCLUDE_PATH=$HOME/.local/include:$HOME/.local/include/elfutils
export CPLUS_INCLUDE_PATH=$HOME/.local/include:$HOME/.local/include/elfutils
export LIBRARY_PATH=$HOME/.local/lib
export LD_LIBRARY_PATH=$HOME/.local/lib

export CONFIG_CONSTRAINTS=$ROOT/workspace/tools/config_constraints.txt

echo '[SUCCESS] Environment variables set successfully.'
