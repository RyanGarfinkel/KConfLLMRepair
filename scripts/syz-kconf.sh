#!/bin/bash
set -e

KERNEL_SRC=$1
OUTPUT=$2
INSTANCE=${3:-upstream-apparmor-kasan}

# Validate Input

if [ -z "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC was not provided.'
    exit 1
fi

if [ ! -d "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC is not a valid directory.'
    exit 1
fi

mkdir -p "$(dirname "$OUTPUT")"

# Run syz-kconf
$SYZ_KCONF -config $MAIN_YML -instance $INSTANCE -sourcedir $KERNEL_SRC

cp "$SYZKALLER_SRC/dashboard/config/linux/$INSTANCE.config" "$OUTPUT"
