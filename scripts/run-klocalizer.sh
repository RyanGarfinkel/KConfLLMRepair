#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
CONSTRAINTS_FILE=$2
LOG_FILE=$3

# Validate Dependencies
if [ -z "$SUPERC_PATH" ] && [ ! -f "$SUPERC_PATH" ]; then
    echo "[ERROR] Superc Linux script not found at $SUPERC_PATH." > "$LOG_FILE"
    exit 1
fi

if [ -z "$ARCH" ]; then
    echo "[ERROR] ARCH environment variable is not set." > "$LOG_FILE"
    exit 1
fi
if [ ! -f "$CONSTRAINTS_FILE" ]; then
    echo "[ERROR] Constraints file $CONSTRAINTS_FILE does not exist." > "$LOG_FILE"
    exit 1
fi

# Running KLocalizer
cd $KERNEL_SRC
rm -f "$LOG_FILE"

LLVM=1 CC="clang -fintegrated-as" LD=ld.lld \
        klocalizer -a x86_64 \
        --repair "$KERNEL_SRC/.config" \
        --config-mutex-file $CONSTRAINTS_FILE 2>&1 || \
    { cd "$WORKING_DIR"; exit 1; }

mv "0-$ARCH.config" ".config"
make LLVM=1 ARCH=$ARCH olddefconfig

cd "$WORKING_DIR"
