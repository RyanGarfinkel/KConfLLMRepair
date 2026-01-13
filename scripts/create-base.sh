#!/bin/bash
set -e

WORKING_DIR=$(pwd)

if [ -z "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC is not set. Please run activate.sh'
    exit 1
fi

# Variables
KVM_GUEST_CONFIG=$KERNEL_SRC/kernel/configs/kvm_guest.config
MERGE_CONFIG=$KERNEL_SRC/scripts/kconfig/merge_config.sh

echo '[INFO] Creating base configuration...'

# Clean the Kernel Repository
cd "$KERNEL_SRC"
make mrproper > /dev/null

# Making the Base Configuration
make defconfig > /dev/null
$MERGE_CONFIG -m '.config' "$KVM_GUEST_CONFIG"
make olddefconfig > /dev/null

DIR=$(dirname "$BASE_CONFIG")
mkdir -p "$DIR"
cp .config "$BASE_CONFIG"

echo "[SUCCESS] Base configuration created at: $BASE_CONFIG"

# Building the kernel
echo '[INFO] Building the kernel...'

LOG_FILE="$DIR/build.log"

sh "$WORKING_DIR/scripts/build-kernel.sh $KERNEL_SRC $BASE_CONFIG $LOG_FILE" || \
    { echo "Failed to build the kernel. Check $LOG_FILE for details." >&2; exit 1; }

echo '[SUCCESS] Kernel built successfully.'

# QEMU Test
echo '[INFO] Testing the kernel with QEMU...'

BZ_IMG="$KERNEL_SRC/arch/$ARCH/boot/bzImage"
LOG_FILE="$DIR/qemu.log"

sh "$WORKING_DIR/scripts/qemu-test.sh" "$KERNEL_SRC" "$BZ_IMG" "$LOG_FILE" || \
    { echo "QEMU test failed. Check $LOG_FILE for details." >&2; exit 1; }

echo '[SUCCESS] QEMU test passed successfully.'
