#!/bin/bash
set -e

WORKING_DIR=$(pwd)

if [ $# -ne 4 ]; then
    echo "Usage: $0 <kernel_source> <output> <seed> <arch>"
    exit 1
fi

# Input
KERNEL_SRC=$1
OUTPUT=$2
SEED=$3
ARCH=$4

if [ ! -d "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC is not a valid directory.'
    exit 1
fi

cd "$KERNEL_SRC" || exit 1

export KCONFIG_SEED=$SEED
make.cross ARCH="$ARCH" randconfig || exit 1

cp .config "$OUTPUT" || exit 1

cd "$WORKING_DIR" || exit 1
