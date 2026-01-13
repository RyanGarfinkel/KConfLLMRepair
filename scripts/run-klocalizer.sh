#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
PATCH_FILE=$2
LOG_FILE=$3
EXTRA_ARGS=("${@:4}")

# Validate Dependencies
if [ -z "$SUPERC_PATH" ] && [ ! -f "$SUPERC_PATH" ]; then
    echo "[ERROR] Superc Linux script not found at $SUPERC_PATH." > "$LOG_FILE"
    exit 1
fi

if [ -z "$ARCH" ]; then
    echo "[ERROR] ARCH environment variable is not set." > "$LOG_FILE"
    exit 1
fi
if [ ! -f "$PATCH_FILE" ]; then
    echo "[ERROR] Patch file $PATCH_FILE does not exist." > "$LOG_FILE"
    exit 1
fi

# Running KLocalizer
cd $KERNEL_SRC
rm -f "$LOG_FILE"

klocalizer --superc-linux-script "$SUPERC_PATH" \
           --include-mutex "$PATCH_FILE" \
           --cross-compiler gcc \
           --arch "$ARCH" \
           "${EXTRA_ARGS[@]}" > "$LOG_FILE" 2>&1 || \
    { cd "$WORKING_DIR"; exit 1; }

mv "0-$ARCH.config" ".config"

cd "$WORKING_DIR"