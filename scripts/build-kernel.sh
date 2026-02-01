#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
LOG_FILE=$2
JOB_COUNT=${3:-$(nproc)}

# Validate Config File
if [ ! -f "$KERNEL_SRC/.config" ]; then
    echo "[ERROR] Configuration file .config does not exist in $KERNEL_SRC." > "$LOG_FILE"
    exit 1
fi

cd "$KERNEL_SRC"

make LLVM=1 ARCH=$ARCH olddefconfig

# Building the kernel
rm -f $LOG_FILE

make -j$JOB_COUNT LLVM=1 ARCH=$ARCH bzImage > $LOG_FILE 2>&1 || \
    { exit 1; }

cd $WORKING_DIR
