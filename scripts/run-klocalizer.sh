#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL=$1
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
cd $KERNEL
rm -f "$LOG_FILE"

echo "[INFO] Running KLocalizer on kernel source at $KERNEL with patch $PATCH_FILE."

LLVM=1 CC="clang -fintegrated-as" LD=ld.lld \
        klocalizer -a $ARCH \
        --repair "$KERNEL/.config" \
        --include-mutex $PATCH_FILE \
        "${EXTRA_ARGS[@]}" > "$LOG_FILE" 2>&1 || \
    { cd "$WORKING_DIR"; exit 1; }

# --constraints-file $CONFIG_CONSTRAINTS \

mv "0-$ARCH.config" ".config"
make LLVM=1 ARCH=$ARCH olddefconfig

cd "$WORKING_DIR"
