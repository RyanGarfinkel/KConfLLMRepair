#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
LOG_FILE=$2
ARCH=$3
BZIMAGE=$4
JOB_COUNT=${5:-$(nproc)}

# Validate Config File
if [ ! -f "$KERNEL_SRC/.config" ]; then
    echo "[ERROR] Configuration file .config does not exist in $KERNEL_SRC." > "$LOG_FILE"
    exit 1
fi

cd "$KERNEL_SRC"

make.cross LLVM=1 ARCH="$ARCH" olddefconfig

# Building the kernel
rm -f $LOG_FILE

make.cross -j$JOB_COUNT LLVM=1 ARCH="$ARCH" "$(basename $BZIMAGE)" > $LOG_FILE 2>&1 || \
    { exit 1; }

cd $WORKING_DIR
