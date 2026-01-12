#!/bin/bash
set -e

if [ -z "$KERNEL_SRC" ]; then
    echo '[ERROR] KERNEL_SRC is not set. Please run activate.sh'
    exit 1
fi

KVM_GUEST_CONFIG=$KERNEL_SRC/kernel/configs/kvm_guest.config
MERGE_CONFIG=$KERNEL_SRC/scripts/kconfig/merge_config.sh

echo '[INFO] Creating base configuration...'

# Clean the Kernel Repository
cd $KERNEL_SRC
make mrproper > /dev/null

# Making the Base Configuration
make defconfig > /dev/null
$MERGE_CONFIG -m '.config' "$KVM_GUEST_CONFIG"
make olddefconfig > /dev/null

DIR=$(dirname "$BASE_CONFIG")
mkdir -p $DIR
cp .config $BASE_CONFIG

echo '[SUCCESS] Base configuration created at: '$BASE_CONFIG


# Building the kernel
echo '[INFO] Building the kernel...'

LOG_FILE="$DIR/build.log"
rm -f $LOG_FILE

make -j$(nproc) LD=ld.lld ARCH=$ARCH CROSS_COMPILE=$CROSS_COMPILE bzImage > $LOG_FILE 2>&1 || \
    { echo "Failed to build the kernel. Check $LOG_FILE for details." >&2; exit 1; }

echo '[SUCCESS] Kernel built successfully.'

# QEMU Test
echo '[INFO] Testing the kernel with QEMU...'

BZ_IMG=$KERNEL_SRC/arch/$ARCH/boot/bzImage
LOG_FILE="$DIR/qemu.log"
rm -f $LOG_FILE

qemu-system-x86_64 -m 2G -smp 1 -kernel $BZ_IMG \
    -append "console=ttyS0 root=/dev/vda1 ro earlyprintk=serial net.ifnames=0 selinux=0 systemd.mask=networking.service systemd.mask=ifupdown-pre.service systemd.mask=systemd-rfkill.service" \
    -drive file="$DEBIAN_IMG",format=raw,if=virtio \
    -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
    -net nic,model=virtio \
    -device virtio-rng-pci \
    -cpu max \
    -nographic > "$LOG_FILE" 2>&1 &

SUCCESS_STRING="login:"
TIMEOUT=300

PID=$!

for i in $(seq 1 $TIMEOUT); do
    if ! kill -0 $PID 2>/dev/null; then
        echo '[ERROR] QEMU process died early!'
        cat "$LOG_FILE"
        exit 1
    fi
    if grep -q "$SUCCESS_STRING" $LOG_FILE 2>/dev/null; then
        echo '[SUCCESS] Boot successful! Login prompt detected.'
        kill $PID 2>/dev/null || true
        wait $PID 2>/dev/null || true
        exit 0
    fi
    sleep 1
done

kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
echo "[ERROR] Boot failed. Check $LOG_FILE for details."
exit 1
