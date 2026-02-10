#!/bin/bash
set -e

WORKING_DIR=$(pwd)

if [ $# -ne 2 ]; then
    echo "Usage: $0 <kernel_source> <output>"
    exit 1
fi

# Input
KERNEL_SRC=$1
OUTPUT=$2

if [ ! -d "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC is not a valid directory.'
    exit 1
fi

cd "$KERNEL_SRC" || exit 1
make randconfig || exit 1

cp .config "$OUTPUT" || exit 1

cd "$WORKING_DIR" || exit 1
