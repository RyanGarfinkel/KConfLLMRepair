#!/bin/bash
set -e

ROOT=$(pwd)

# Input

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

cd "$KERNEL_SRC"
make x86_64_defconfig KERNELVERSION=syzkaller KERNELRELEASE=syzkaller \
     LOCALVERSION=-syzkaller -j 16 ARCH=x86_64 LLVM=1 \
     O=/tmp/debug_kconf 2>&1 || echo "[DEBUG] Make failed with exit code $?"
cd "$ROOT"

# Run syz-kconf
$SYZ_KCONF -config $MAIN_YML -instance $INSTANCE -sourcedir $KERNEL_SRC

cp "$SYZKALLER_SRC/dashboard/config/linux/$INSTANCE.config" "$KERNEL_SRC/.config"

cd "$KERNEL_SRC"
make LLVM=1 olddefconfig ARCH=$ARCH # > /dev/null
cd "$ROOT"

cp "$KERNEL_SRC/.config" "$OUTPUT"
