#!/bin/bash

set -e

DEST_DIR=$WORKSPACE/data/base
mkdir -p "$DEST_DIR"
DEST=$DEST_DIR/base.config

KVM_GUEST_CONFIG=$KERNEL_SRC/kernel/configs/kvm_guest.config

# Clean repository
cd $KERNEL_SRC
make mrproper

# Base configuration file
echo "Generating base configuration..."

make defconfig
$KERNEL_SRC/scripts/kconfig/merge_config.sh -m ".config" "$KVM_GUEST_CONFIG"
make olddefconfig

cp .config $DEST
echo "Base configuration generated at $DEST"
echo "Confirming that the base configuration boots..."

# Building the kernel
echo "Building the kernel..."
export PATH="/usr/lib/ccache:$PATH"
make -j$(nproc) LD=ld.lld ARCH=$ARCH CROSS_COMPILE="$ARCH-linux-gnu-" bzImage > $DEST_DIR/build.log 2>&1 || \
    { echo "Failed to build the kernel. Check $DEST_DIR/build.log for details." >&2; exit 1; }

echo "Kernel built successfully. Starting QEMU test..."

BZ_IMG=$KERNEL_SRC/arch/$ARCH/boot/bzImage
LOG_FILE=$DEST_DIR/qemu.log
rm -f $LOG_FILE

# QEMU Test
qemu-system-x86_64 -m 2G -smp 1 -kernel $BZ_IMG \
    -append "console=ttyS0 root=/dev/vda1 ro earlyprintk=serial net.ifnames=0 selinux=0 systemd.mask=networking.service systemd.mask=ifupdown-pre.service systemd.mask=systemd-rfkill.service" \
    -drive file="$DEBIAN_IMG",format=raw,if=virtio \
    -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
    -net nic,model=virtio \
    -device virtio-rng-pci \
    -cpu max \
    -nographic \
    -pidfile "$DEST_DIR/qemu.pid" > "$LOG_FILE" 2>&1 &

TIMEOUT=1320
SUCCESS_STRING="login:"
PID=$!

for i in $(seq 1 $TIMEOUT); do
    if ! kill -0 $PID 2>/dev/null; then
        echo "QEMU process died early!"
        cat "$LOG_FILE"
        exit 1
    fi
    if grep -q "$SUCCESS_STRING" $LOG_FILE 2>/dev/null; then
        echo "Boot successful! Login prompt detected."
        kill $PID 2>/dev/null || true
        exit 0
    fi
    sleep 1
done

kill $PID 2>/dev/null || true
echo "Boot failed. Check $LOG_FILE for details."
exit 1

# #!/bin/bash

# set -e

# # Base configuration file
# echo "Generating base configuration..."

# SYZKALLER_CONFIG=$SYZKALLER_SRC/dashboard/config/linux/upstream-apparmor-kasan.config
# KVM_GUEST_CONFIG=$KERNEL_SRC/kernel/configs/kvm_guest.config

# DEST_DIR=$WORKSPACE/data/base
# mkdir -p "$DEST_DIR"

# DEST=$DEST_DIR/base.config

# export KCONFIG_CONFIG=$KERNEL_SRC/.config

# echo "Merging syzkaller and kvm configs..."
# $KERNEL_SRC/scripts/kconfig/merge_config.sh -m "$SYZKALLER_CONFIG" "$KVM_GUEST_CONFIG"

# echo "Running make olddefconfig..."
# cd $KERNEL_SRC
# make olddefconfig

# OPTIMIZED_CMDLINE="console=ttyS0 root=/dev/vda rw earlyprintk=serial net.ifnames=0 systemd.mask=networking.service systemd.mask=ifupdown-pre.service systemd.mask=systemd-rfkill.service vivid.n_devs=4 systemd.default_timeout_start_sec=10"
# ./scripts/config --file .config --set-str CMDLINE "$OPTIMIZED_CMDLINE"
# ./scripts/config --file .config --enable CMDLINE_OVERRIDE
# make olddefconfig

# cp .config $DEST

# echo "Base configuration generated at $DEST"

# echo "Confirming that the base configuration boots..."

# # Building the kernel
# echo "Building the kernel..."
# export PATH="/usr/lib/ccache:$PATH"
# make -j$(nproc) LD=ld.lld ARCH=$ARCH CROSS_COMPILE="$ARCH-linux-gnu-" bzImage > $DEST_DIR/build.log 2>&1 || \
#     { echo "Failed to build the kernel. Check $DEST_DIR/build.log for details." >&2; exit 1; }

# echo "Kernel built successfully. Starting QEMU test..."

# BZ_IMG=$KERNEL_SRC/arch/$ARCH/boot/bzImage
# LOG_FILE=$DEST_DIR/qemu.log
# rm -f $LOG_FILE

# # QEMU Test
# # qemu-system-$ARCH -m 2G -smp 2 -kernel $BZ_IMG \
# #     -append "console=ttyS0 earlyprintk=serial,ttyS0 root=/dev/vda rw net.ifnames=0 systemd.mask=networking.service systemd.mask=ifupdown-pre.service systemd.mask=systemd-rfkill.service vivid.n_devs=4 systemd.default_timeout_start_sec=10" \
# #     -drive file=$BULLSEYE_IMG,format=raw,if=virtio \
# #     -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
# #     -net nic,model=virtio \
# #     -nographic > $LOG_FILE 2>&1 &

# qemu-system-$ARCH -m 2G -smp 1 -kernel $BZ_IMG \
#     -append "console=ttyS0 root=/dev/vda rw earlyprintk=serial net.ifnames=0 systemd.mask=networking.service systemd.mask=ifupdown-pre.service systemd.mask=systemd-rfkill.service systemd.default_timeout_start_sec=10" \
#     -drive file=$BULLSEYE_IMG,format=raw,if=virtio \
#     -net user,host=10.0.2.10,hostfwd=tcp:127.0.0.1:10022-:22 \
#     -net nic,model=virtio \
#     -device virtio-rng-pci \
#     -cpu max \
#     -nographic \
#     -pidfile $DEST_DIR/qemu.pid > $LOG_FILE 2>&1 &

# TIMEOUT=1320
# SUCCESS_STRING="login:"
# PID=$!

# for i in $(seq 1 $TIMEOUT); do
#     if ! kill -0 $PID 2>/dev/null; then
#         echo "QEMU process died early!"
#         cat "$LOG_FILE"
#         exit 1
#     fi
#     if grep -q "$SUCCESS_STRING" $LOG_FILE 2>/dev/null; then
#         echo "Boot successful! Login prompt detected."
#         kill $PID 2>/dev/null || true
#         exit 0
#     fi
#     sleep 1
# done

# kill $PID 2>/dev/null || true
# echo "Boot failed. Check $LOG_FILE for details."
# exit 1
