#!/bin/bash
set -e

WORKING_DIR=$(pwd)

# Input
KERNEL_SRC=$1
IMG=$2
LOG_FILE=$3
ARCH=$4
DEBIAN_IMG=$5
TIMEOUT=${6:-300} # 5m Default

# Variables
SUCCESS_STRING='login:'
MAINTENANCE_STRING='Press Enter for maintenance'

# Running QEMU
rm -f "$LOG_FILE"
cd "$WORKING_DIR"

if [ "$ARCH" = "arm64" ]; then
    qemu-system-aarch64 \
        -machine virt \
        -cpu cortex-a57 \
        -nographic \
        -smp 1 \
        -drive file="$DEBIAN_IMG",format=raw,file.locking=off \
        -kernel "$IMG" \
        -append "console=ttyAMA0 root=/dev/vda oops=panic panic_on_warn=1 panic=-1 ftrace_dump_on_oops=orig_cpu debug earlyprintk=serial slub_debug=UZ" \
        -m 2G \
        -net user \
        -net nic > "$LOG_FILE" 2>&1 &
else
    qemu-system-x86_64 \
        -m 2G \
        -smp 2 \
        -kernel "$IMG" \
        -append "console=ttyS0 root=/dev/sda earlyprintk=serial net.ifnames=0" \
        -drive file="$DEBIAN_IMG",format=raw,file.locking=off \
        -net user,host=10.0.2.10 \
        -net nic,model=e1000 \
        -enable-kvm \
        -nographic > "$LOG_FILE" 2>&1 &
fi

# Waiting for Login Prompt
PID=$!

for i in $(seq 1 $TIMEOUT); do
    if ! kill -0 $PID 2>/dev/null; then
        echo '[ERROR] QEMU process died early!'
        cd "$WORKING_DIR"
        exit 1
    fi
    if grep -q "$SUCCESS_STRING" "$LOG_FILE" 2>/dev/null; then
        echo '[SUCCESS] Boot successful! Login prompt detected.'
        kill $PID 2>/dev/null || true
        cd "$WORKING_DIR"
        exit 0
    fi
    if grep -q "$MAINTENANCE_STRING" "$LOG_FILE" 2>/dev/null; then
        echo '[SUCCESS] Boot successful! Emergency maintenance prompt detected.'
        kill $PID 2>/dev/null || true
        cd "$WORKING_DIR"
        exit 2
    fi
    sleep 1
done

kill $PID 2>/dev/null || true
echo "[ERROR] Boot failed. Check $LOG_FILE for details."
cd "$WORKING_DIR"
exit 1
