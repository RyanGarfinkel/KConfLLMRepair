#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
LOG_FILE=$2
JOB_COUNT=${3:-$(nproc)}

# Validate Config File
if [ ! -f "$KERNEL_SRC/.config" ]; then
    echo "[ERROR] Configuration file .config does not exist in $KERNEL_SRC." > "$LOG_FILE"
    exit 1
fi

cd "$KERNEL_SRC"

make olddefconfig > /dev/null

# sed -i 's/#define PERCPU_FIRST_CHUNK_RESERVE\s\+4096/#define PERCPU_FIRST_CHUNK_RESERVE  8192/' \
#     arch/x86/include/asm/percpu.h

# Building the kernel
rm -f $LOG_FILE

# make -j$JOB_COUNT LD=ld.lld ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE bzImage > $LOG_FILE 2>&1 || \
make -j$JOB_COUNT LD=ld.lld ARCH=$ARCH CC="ccache gcc" CROSS_COMPILE=$CROSS_COMPILE bzImage > $LOG_FILE 2>&1 || \
    { exit 1; }

cd $WORKING_DIR
