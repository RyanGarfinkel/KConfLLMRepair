#!/bin/bash
set -e

WORKING_DIR=$(pwd)

if [ $# -ne 3 ]; then
    echo "Usage: $0 <kernel_source> <output> <seed>"
    exit 1
fi

# Input
KERNEL_SRC=$1
OUTPUT=$2
SEED=$3

if [ ! -d "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC is not a valid directory.'
    exit 1
fi

cd "$KERNEL_SRC" || exit 1

export KCONFIG_SEED=$SEED
make randconfig || exit 1

cp .config "$OUTPUT" || exit 1

cd "$WORKING_DIR" || exit 1
