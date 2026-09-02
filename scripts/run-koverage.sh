#!/bin/bash

# Input
KERNEL_SRC=$1
CONFIG=$2
PATCH_FILE=$3
LOG_FILE=$4
ARCH=$5

OUT_DIR=$(dirname "$LOG_FILE")
OUTPUT_FILE="$OUT_DIR/coverage_report.json"

# Validate Dependencies
if [ -z "$SUPERC_PATH" ] || [ ! -f "$SUPERC_PATH" ]; then
    echo "[ERROR] Superc Linux script not found at $SUPERC_PATH." > "$LOG_FILE"
    exit 1
fi

if [ -z "$ARCH" ]; then
    echo "[ERROR] ARCH parameter is not set." > "$LOG_FILE"
    exit 1
fi

if [ ! -f "$CONFIG" ]; then
    echo "[ERROR] Config file $CONFIG does not exist." > "$LOG_FILE"
    exit 1
fi

if [ ! -f "$PATCH_FILE" ]; then
    echo "[ERROR] Patch file $PATCH_FILE does not exist." > "$LOG_FILE"
    exit 1
fi

# Running koverage
rm -f "$LOG_FILE" "$OUTPUT_FILE"

LLVM=1 CC="clang -fintegrated-as" LD=ld.lld \
        koverage -a "$ARCH" \
        --linux-ksrc "$KERNEL_SRC" \
        --config "$CONFIG" \
        --check-patch "$PATCH_FILE" \
        -f \
        -o "$OUTPUT_FILE" > "$LOG_FILE" 2>&1

exit $?
