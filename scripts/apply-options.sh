#!/bin/bash

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
LOG_FILE=$2
ARCH=$3
EXTRA_ARGS=("${@:4}")

# Validate Dependencies
if [ -z "$ARCH" ]; then
    echo "[ERROR] ARCH parameter is not set." > "$LOG_FILE"
    exit 1
fi

if [ ! -f "$KERNEL_SRC/scripts/config" ]; then
    echo "[ERROR] scripts/config does not exist in $KERNEL_SRC." > "$LOG_FILE"
    exit 1
fi

if [ ! -f "$KERNEL_SRC/.config" ]; then
    echo "[ERROR] Configuration file .config does not exist in $KERNEL_SRC." > "$LOG_FILE"
    exit 1
fi

# Applying options
cd "$KERNEL_SRC"
rm -f "$LOG_FILE"

scripts/config --file .config "${EXTRA_ARGS[@]}" > "$LOG_FILE" 2>&1 || { cd "$WORKING_DIR"; exit 1; }

make LLVM=1 ARCH=$ARCH olddefconfig >> "$LOG_FILE" 2>&1 || { cd "$WORKING_DIR"; exit 1; }

cd "$WORKING_DIR"
